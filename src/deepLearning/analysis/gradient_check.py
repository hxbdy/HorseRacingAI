# 数値微分の結果と偏微分の結果との差分を確認する
# 差が大きい場合、誤差逆伝播計算式が誤っている可能性が高いことになる
# 理想は 1e-10 以内に納めること

import TwoLayerNet
import numpy as np
import pickle
import configparser
import itertools

# 学習テーブル, 教師テーブル取得
# 学習用データ生成条件取得
# テスト用データ生成条件
from table import *

# load config
config = configparser.ConfigParser()
config.read('./src/path.ini')
path_learningList = config.get('nn', 'path_learningList')
    
# ハイパーパラメータ
iters_num     = 3     # 計算式チェック回数

with open(path_learningList + t_train_file_name, 'rb') as f:
    flat_pkl = []
    flat_pkl_list = pickle.load(f)
    for i in flat_pkl_list:
        flat_pkl.append(list(itertools.chain.from_iterable(i)))
    flat_pkl = np.array(flat_pkl)
    tData = flat_pkl

with open(path_learningList + X_train_file_name, 'rb') as f:
    flat_pkl = []
    flat_pkl_list = pickle.load(f)
    for i in flat_pkl_list:
        flat_pkl.append(list(itertools.chain.from_iterable(i)))
    flat_pkl = np.array(flat_pkl)
    xData = flat_pkl

net = TwoLayerNet.TowLayerNet(155, 40, 24)

for i in range(iters_num):

    # 学習データ取り出し
    batch = np.random.randint(0, 4188)
    
    x = np.array(xData[batch])
    x = x.reshape([1, -1])
    t = np.array(tData[batch])

    # print("x = ", x)
    # print("t = ", t)

    # 勾配計算
    grad_num = net.numerical_gradient(x, t)
    grad_bck = net.gradient(x, t)

    # 各勾配,バイアスの絶対誤差の平均
    for key in grad_num.keys():
        diff = np.average(np.abs(grad_bck[key] - grad_num[key]))
        print(key + " : " + str(diff))
