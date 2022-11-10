from typing import OrderedDict
import numpy as np
import configparser
import shutil
import pickle

from encoding_common import encoding_serial_dir_path, encoding_save_nn_data, dl_newest_dir_path

# load config
config = configparser.ConfigParser()
config.read('./src/path.ini', 'UTF-8')
path_root_trainedParam = config.get('nn', 'path_root_trainedParam')

def softmax(x):
    x = x - np.max(x, axis=-1, keepdims=True)   # オーバーフロー対策
    return np.exp(x) / np.sum(np.exp(x), axis=-1, keepdims=True)

def sum_squared_error(y, t):
    return 0.5 * np.sum((y-t)**2)

def cross_entropy_error(y, t):
    delta=1e-7
    if y.ndim==1:
        t=t.reshape(1,t.size)
        y=y.reshape(1,y.size)
    batch_size=y.shape[0]
    return -np.sum(t*np.log(y+delta))/batch_size

def numerical_gradient(f, x):
    h = 1e-4 # 0.0001
    grad = np.zeros_like(x)
    
    it = np.nditer(x, flags=['multi_index'], op_flags=['readwrite'])
    while not it.finished:
        idx = it.multi_index
        tmp_val = x[idx]
        x[idx] = tmp_val + h
        fxh1 = f(x) # f(x+h)
        
        x[idx] = tmp_val - h 
        fxh2 = f(x) # f(x-h)
        grad[idx] = (fxh1 - fxh2) / (2*h)
        
        x[idx] = tmp_val # 値を元に戻す
        it.iternext()   
        
    return grad

class Relu:
    def __init__(self):
        self.mask = None

    def forward(self, x):
        self.mask = (x <= 0)
        out = x.copy()
        out[self.mask] = 0

        return out

    def backward(self, dout):
        dout[self.mask] = 0
        dx = dout

        return dx

class Affine:
    def __init__(self, W, b):
        self.W = W
        self.b = b
        
        self.x = None
        self.original_x_shape = None
        # 重み・バイアスパラメータの微分
        self.dW = None
        self.db = None

    def forward(self, x):
        # テンソル対応
        self.original_x_shape = x.shape
        x = x.reshape(x.shape[0], -1)
        self.x = x

        out = np.dot(self.x, self.W) + self.b

        return out

    def backward(self, dout):
        dx = np.dot(dout, self.W.T)
        self.dW = np.dot(self.x.T, dout)
        self.db = np.sum(dout, axis=0)
        
        dx = dx.reshape(*self.original_x_shape)  # 入力データの形状に戻す（テンソル対応）
        return dx

class Sigmoid:
    def __init__(self):
        self.out = None

    def forward(self, x):
        out = 1 / (1 + np.exp(-x))
        self.out = out
        return out

    def backward(self, dout):
        dx = dout * (1.0 - self.out) * self.out

        return dx

class SoftmaxWithLoss:
    def __init__(self):
        self.loss = None
        self.y = None # softmaxの出力
        self.t = None # 教師データ

    def forward(self, x, t):
        self.t = t
        self.y = softmax(x)
        self.loss = cross_entropy_error(self.y, self.t)
        #self.loss = sum_squared_error(self.y, self.t)

        return self.loss

    def backward(self, dout=1):
        batch_size = self.t.shape[0]
        if self.t.size == self.y.size: # 教師データがone-hot-vectorの場合
            dx = (self.y - self.t) / batch_size
        else:
            dx = self.y.copy()
            dx[np.arange(batch_size), self.t] -= 1
            dx = dx / batch_size
        
        return dx
class TowLayerNet:
    def __init__(self,input_size,hidden_size,output_size,weight_init_std=0.01):
        self.params={}
        self.params['W1']=weight_init_std*np.random.randn(input_size,hidden_size)
        self.params['b1']=np.zeros(hidden_size)
        self.params['W2']=weight_init_std*np.random.randn(hidden_size,output_size)
        self.params['b2']=np.zeros(output_size)

        # レイヤ
        self.layers = OrderedDict()
        self.layers['Affine1'] = Affine(self.params['W1'], self.params['b1'])
        self.layers['Relu1']   = Relu()
        self.layers['Affine2'] = Affine(self.params['W2'], self.params['b2'])
        self.lastLayer = SoftmaxWithLoss()

    def softmax(self,x):
        '''ソフトマックス関数'''
        c=np.max(x)
        exp_x=np.exp(x-c)
        sum_exp_x=np.sum(exp_x)
        y=exp_x/sum_exp_x
        return y

    def crossEntropyError(self,y,t):
        '''
        交差エントロピー誤差
        y:予想ラベル(ソフトマックス関数の出力)
        t:正解ラベル
        return:0に近いほど正確
        '''
        delta=1e-7
        if y.ndim==1:
            t=t.reshape(1,t.size)
            y=y.reshape(1,y.size)
        batch_size=y.shape[0]
        return -np.sum(t*np.log(y+delta))/batch_size

    def meanSquaredError(self, y, t):
        return 0.5 * np.sum((y-t)**2)
    
    def numerical_gradient(self, x, t):
        '''
        数値微分
        '''
        loss_W = lambda W: self.loss(x, t)
        grads = {}
        grads['W1'] = numerical_gradient(loss_W, self.params['W1'])
        grads['b1'] = numerical_gradient(loss_W, self.params['b1'])
        grads['W2'] = numerical_gradient(loss_W, self.params['W2'])
        grads['b2'] = numerical_gradient(loss_W, self.params['b2'])
        return grads

    def gradient(self, x, t):
        '''偏微分'''

        # forward
        self.loss(x, t)

        # backward
        dout = 1
        dout = self.lastLayer.backward(dout)

        layers = list(self.layers.values())
        layers.reverse()
        for layer in layers:
            dout = layer.backward(dout)

        grads = {}
        grads['W1'] = self.layers['Affine1'].dW
        grads['b1'] = self.layers['Affine1'].db
        grads['W2'] = self.layers['Affine2'].dW
        grads['b2'] = self.layers['Affine2'].db

        return grads

    def predict(self,x):
        '''
        推論を行う
        '''
        for layer in self.layers.values():
            x = layer.forward(x)
        return x

    def hit(self, x, t, odds, bet, grade):
        wallet = 0
        g1 = 0
        g2 = 0
        g3 = 0

        y = self.predict(x)
        y = np.argmax(y, axis=1)
        if t.ndim != 1 : t = np.argmax(t, axis=1)
        
        for idx in range(y.shape[0]):
            wallet -= bet
            if y[idx] == t[idx]:
                wallet += odds[idx] * bet
                if grade[idx] == 1:
                    g1 += 1
                elif grade[idx] == 2:
                    g2 += 1
                elif grade[idx] == 3:
                    g3 += 1
        
        return wallet, (g1, g2, g3)

    def accuracy(self, x, t):
        y = self.predict(x)
        y = np.argmax(y, axis=1)
        if t.ndim != 1 : t = np.argmax(t, axis=1)
        
        accuracy = np.sum(y == t) / float(x.shape[0])
        return accuracy

    def loss(self,x,t):
        y=self.predict(x)
        return self.lastLayer.forward(y, t)

    def seveParam(self):
        '''各パラメータを保存する'''
        # 連番取得
        serial_dir_path = encoding_serial_dir_path(path_root_trainedParam)
        # 連番フォルダに保存
        encoding_save_nn_data(serial_dir_path, "W1.pickle", self.params['W1'])
        encoding_save_nn_data(serial_dir_path, "b1.pickle", self.params['b1'])
        encoding_save_nn_data(serial_dir_path, "W2.pickle", self.params['W2'])
        encoding_save_nn_data(serial_dir_path, "b2.pickle", self.params['b2'])

        # 最新フォルダにもコピー
        # 最新フォルダまでのパスを取得
        newest_dir_path = dl_newest_dir_path()
        # newestフォルダ削除
        shutil.rmtree(newest_dir_path)
        # 最新フォルダに結果をコピー
        shutil.copytree(serial_dir_path, newest_dir_path)

    def loadParam(self):
        '''最新フォルダから各パラメータを読み込む'''
        newest_dir_path = dl_newest_dir_path()
        with open(newest_dir_path + "W1.pickle", 'rb') as f:
            self.params['W1'] = pickle.load(f)
        with open(newest_dir_path + "b1.pickle", 'rb') as f:
            self.params['b1'] = pickle.load(f)
        with open(newest_dir_path + "W2.pickle", 'rb') as f:
            self.params['W2'] = pickle.load(f)
        with open(newest_dir_path + "b2.pickle", 'rb') as f:
            self.params['b2'] = pickle.load(f)

        # レイヤ
        # TODO:コンストラクタでも同じことをしているので要リファクタ
        self.layers = OrderedDict()
        self.layers['Affine1'] = Affine(self.params['W1'], self.params['b1'])
        self.layers['Relu1']   = Relu()
        self.layers['Affine2'] = Affine(self.params['W2'], self.params['b2'])
        self.lastLayer = SoftmaxWithLoss()
