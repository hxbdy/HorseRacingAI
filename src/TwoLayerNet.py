import numpy as np
import os
import sys

class TowLayerNet:
    def __init__(self,input_size,hidden_size,output_size,weight_init_std=0.01):
        self.params={}
        self.params['W1']=weight_init_std*np.random.randn(input_size,hidden_size)
        self.params['b1']=np.zeros(hidden_size)
        self.params['W2']=weight_init_std*np.random.randn(hidden_size,output_size)
        self.params['b2']=np.zeros(output_size)

    def sigmoid(self,x):
        '''シグモイド関数'''
        return 1/(1+np.exp(-x))

    def sigmoidGrad(self,x):
        '''シグモイド勾配関数'''
        return (1.0 - self.sigmoid(x)) * self.sigmoid(x)

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

    def gradient(self, x, t):
        '''偏微分'''
        W1, W2 = self.params['W1'], self.params['W2']
        b1, b2 = self.params['b1'], self.params['b2']
        grads = {}

        # テンソル以上に対応
        batch_num = x.shape[0]

        # forward
        a1 = np.dot(x, W1) + b1
        z1 = self.sigmoid(a1)
        a2 = np.dot(z1, W2) + b2
        y = self.softmax(a2)

        # backward
        dy = (y - t) / batch_num
        grads['W2'] = np.dot(z1.T, dy)
        grads['b2'] = np.sum(dy, axis=0)

        da1 = np.dot(dy, W2.T)
        dz1 = self.sigmoidGrad(a1) * da1
        grads['W1'] = np.dot(x.T, dz1)
        grads['b1'] = np.sum(dz1, axis=0)

        return grads

    def predict(self,x):
        '''
        推論を行う
        '''
        W1=self.params['W1']
        W2=self.params['W2']
        b1=self.params['b1']
        b2=self.params['b2']
        a1=np.dot(x,W1)+b1
        z1=self.sigmoid(a1)
        a2=np.dot(z1,W2)+b2
        y=self.softmax(a2)
        return y

    def loss(self,x,t):
        y=self.predict(x)
        return self.crossEntropyError(y,t)

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
        path_w='../trainedParam/gradient'+par+'.txt'
        f=open(path_w,mode='w')
        it = np.nditer(self.params[par], flags=['multi_index'], op_flags=['readwrite'])
        while not it.finished:
            idx=it.multi_index
            f.write(str(self.params[par][idx]))
            f.write("\n")
            it.iternext()
        f.close()

    def saveLoss(self,loss):
        path_w='../trainedParam/loss.txt'
        f=open(path_w,mode='w')
        for i in loss:
            f.write(str(i)+"\n")
        f.close()

    def loadGradient(self,par):
        '''
        勾配を読みこむ
        '''
        path_r='../trainedParam/gradient'+par+'.txt'
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
