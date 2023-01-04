from typing import OrderedDict
import pickle
import os

from file_path_mgr import path_ini
import xross
np = xross.facttory_xp()

from encoding_common import encoding_save_nn_data, dl_newest_dir_path

# load config
path_root_trainedParam = path_ini('nn', 'path_root_trainedParam')

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

class BatchNormalization:
    """
    http://arxiv.org/abs/1502.03167
    """
    def __init__(self, gamma, beta, momentum=0.9, running_mean=None, running_var=None):
        self.gamma = gamma
        self.beta = beta
        self.momentum = momentum
        self.input_shape = None # Conv層の場合は4次元、全結合層の場合は2次元  

        # テスト時に使用する平均と分散
        self.running_mean = running_mean
        self.running_var = running_var  
        
        # backward時に使用する中間データ
        self.batch_size = None
        self.xc = None
        self.std = None
        self.dgamma = None
        self.dbeta = None

    def forward(self, x, train_flg=True):
        self.input_shape = x.shape
        if x.ndim != 2:
            N, C, H, W = x.shape
            x = x.reshape(N, -1)

        out = self.__forward(x, train_flg)
        
        return out.reshape(*self.input_shape)
            
    def __forward(self, x, train_flg):
        if self.running_mean is None:
            N, D = x.shape
            self.running_mean = np.zeros(D)
            self.running_var = np.zeros(D)
                        
        if train_flg:
            mu = x.mean(axis=0)
            xc = x - mu
            var = np.mean(xc**2, axis=0)
            std = np.sqrt(var + 10e-7)
            xn = xc / std
            
            self.batch_size = x.shape[0]
            self.xc = xc
            self.xn = xn
            self.std = std
            self.running_mean = self.momentum * self.running_mean + (1-self.momentum) * mu
            self.running_var = self.momentum * self.running_var + (1-self.momentum) * var            
        else:
            xc = x - self.running_mean
            xn = xc / ((np.sqrt(self.running_var + 10e-7)))
            
        out = self.gamma * xn + self.beta 
        return out

    def backward(self, dout):
        if dout.ndim != 2:
            N, C, H, W = dout.shape
            dout = dout.reshape(N, -1)

        dx = self.__backward(dout)

        dx = dx.reshape(*self.input_shape)
        return dx

    def __backward(self, dout):
        dbeta = dout.sum(axis=0)
        dgamma = np.sum(self.xn * dout, axis=0)
        dxn = self.gamma * dout
        dxc = dxn / self.std
        dstd = -np.sum((dxn * self.xc) / (self.std * self.std), axis=0)
        dvar = 0.5 * dstd / self.std
        dxc += (2.0 / self.batch_size) * self.xc * dvar
        dmu = np.sum(dxc, axis=0)
        dx = dxc - dmu / self.batch_size
        
        self.dgamma = dgamma
        self.dbeta = dbeta
        
        return dx
class TowLayerNet:
    def __init__(self,input_size,hidden_size,output_size):
        self.params={}

        # 標準偏差weight_init_stdで各パラメータ初期化
        # 過去のパラメータの互換のため残しておく
        # weight_init_std=0.01
        # self.params['W1']=weight_init_std*np.random.randn(input_size,hidden_size)
        # self.params['b1']=np.zeros(hidden_size)
        # self.params['W2']=weight_init_std*np.random.randn(hidden_size,output_size)
        # self.params['b2']=np.zeros(output_size)

        # He の初期化
        self.params['W1']=np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.params['b1']=np.zeros(hidden_size)
        self.params['W2']=np.random.randn(hidden_size, output_size) * np.sqrt(2.0 / hidden_size)
        self.params['b2']=np.zeros(output_size)

        # BatchNormalization用パラメータ初期化
        # TODO: 有効無効切り替え可能にする
        # self.params['gamma1'] = np.ones(hidden_size)
        # self.params['beta1'] = np.zeros(hidden_size)

        # レイヤ初期化
        self._init_layer()

    def _init_layer(self):
        self.layers = OrderedDict()
        self.layers['Affine1'] = Affine(self.params['W1'], self.params['b1'])
        # TODO: 有効無効切り替え可能にする
        # self.layers['BatchNorm1'] = BatchNormalization(self.params['gamma1'], self.params['beta1'])
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
        # TODO: 有効無効切り替え可能にする
        # grads['gamma1'] = self.layers['BatchNorm1'].dgamma
        # grads['beta1'] = self.layers['BatchNorm1'].dbeta

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

        # weight decay
        # 過学習抑制
        # 抑制有効時はBatchNormalizationは無効が一般的？
        weight_decay = 0
        weight_decay_lambda = 0.1 # 係数, 0なら抑制しない

        W1 = self.params['W1']
        weight_decay += 0.5 * weight_decay_lambda * np.sum(W1 ** 2)

        W2 = self.params['W2']
        weight_decay += 0.5 * weight_decay_lambda * np.sum(W2 ** 2)

        return self.lastLayer.forward(y, t) + weight_decay

    def seveParam(self, serial_dir_path):
        '''各パラメータを保存する'''
        os.makedirs(serial_dir_path, exist_ok=True)
        # 連番フォルダに保存
        encoding_save_nn_data(serial_dir_path, "W1.pickle", self.params['W1'])
        encoding_save_nn_data(serial_dir_path, "b1.pickle", self.params['b1'])
        encoding_save_nn_data(serial_dir_path, "W2.pickle", self.params['W2'])
        encoding_save_nn_data(serial_dir_path, "b2.pickle", self.params['b2'])

    def loadParam(self, flg="newest"):
        # 学習パラメータ読み込み
        # デフォルトでは最新フォルダから読み込む
        if flg == "newest":
            newest_dir_path = dl_newest_dir_path()
        elif flg == "init":
            newest_dir_path = dl_newest_dir_path() + "init/"
        else:
            pass

        with open(newest_dir_path + "W1.pickle", 'rb') as f:
            self.params['W1'] = pickle.load(f)
        with open(newest_dir_path + "b1.pickle", 'rb') as f:
            self.params['b1'] = pickle.load(f)
        with open(newest_dir_path + "W2.pickle", 'rb') as f:
            self.params['W2'] = pickle.load(f)
        with open(newest_dir_path + "b2.pickle", 'rb') as f:
            self.params['b2'] = pickle.load(f)

        # レイヤ初期化
        self._init_layer()
