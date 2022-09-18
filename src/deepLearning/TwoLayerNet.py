from typing import OrderedDict
import numpy as np
import os
import sys
import pathlib

# commonフォルダ内読み込みのため
deepLearning_dir = pathlib.Path(__file__).parent
src_dir = deepLearning_dir.parent
root_dir = src_dir.parent
dir_lst = [deepLearning_dir, src_dir, root_dir]
for dir_name in dir_lst:
    if str(dir_name) not in sys.path:
        sys.path.append(str(dir_name))

OUTPUT_PATH = str(root_dir) + "\\dst\\trainedParam\\"

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
        self.W =W
        self.b = b

        self.x = None
        # 重み・バイアスパラメータの微分
        self.dW = None
        self.db = None

    def forward(self, x):
        self.x = x
        out = np.dot(self.x, self.W) + self.b

        return out

    def backward(self, dout):
        dx = np.dot(dout, self.W.T)
        self.dW = np.dot(self.x.T, dout)
        self.db = np.sum(dout, axis=0)

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
        # batch_size = self.t.shape[0]
        dx = (self.y - self.t) #/ batch_size
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

    def loss(self,x,t):
        y=self.predict(x)
        return self.lastLayer.forward(y, t)

    def loadTest(self,path,data_max):
        '''
        入力データの読み込み
        標準化はここで行う
        '''
        x_test=[]
        return x_test

    def loadTrain(self,path,data_max,teach):
        '''
        教師データの読み込み
        標準化はここで行う
        '''
        x_train=[]
        t_train=[]
        return x_train,t_train

    def saveGradient(self,par):
        '''
        勾配をテキストに保存する
        '''
        # 保存先フォルダの存在確認
        os.makedirs(OUTPUT_PATH, exist_ok=True)
        path_w=OUTPUT_PATH+par+'.txt'
        f=open(path_w,mode='w')
        it = np.nditer(self.params[par], flags=['multi_index'], op_flags=['readwrite'])
        while not it.finished:
            idx=it.multi_index
            f.write(str(self.params[par][idx]))
            f.write("\n")
            it.iternext()
        f.close()

    def saveLoss(self,loss):
        # 保存先フォルダの存在確認
        os.makedirs(OUTPUT_PATH, exist_ok=True)
        path_w=OUTPUT_PATH+'loss.txt'
        f=open(path_w,mode='w')
        for i in loss:
            f.write(str(i)+"\n")
        f.close()

    def loadGradient(self,par):
        '''
        勾配を読みこむ
        '''
        # 保存先フォルダの存在確認
        os.makedirs(OUTPUT_PATH, exist_ok=True)
        path_r=OUTPUT_PATH+par+'.txt'
        with open(path_r) as f:
            l = f.readlines()

        it = np.nditer(self.params[par], flags=['multi_index'], op_flags=['readwrite'])
        cnt=0
        while not it.finished:
            idx=it.multi_index
            self.params[par][idx]=l[cnt]
            it.iternext()
            cnt+=1

    def seveParam(self):
        '''各パラメータを保存する'''
        self.saveGradient('W1')
        self.saveGradient('b1')
        self.saveGradient('W2')
        self.saveGradient('b2')

    def loadParam(self):
        '''各パラメータを設定する'''
        self.loadGradient('W1')
        self.loadGradient('b1')
        self.loadGradient('W2')
        self.loadGradient('b2')
