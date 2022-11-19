# 数値微分の結果と偏微分の結果との差分を確認する
# 差が大きい場合、誤差逆伝播計算式が誤っている可能性が高いことになる
# 理想は 1e-10 以内に納めること
# > python src/deepLearning/analysis/gradient_check.py

import TwoLayerNet
import numpy as np
import configparser

from encoding_common import encoding_load, dl_flat2d

# load config
config = configparser.ConfigParser()
config.read('./src/path.ini', 'UTF-8')
path_learningList = config.get('nn', 'path_learningList')

# 学習データの読込
config = configparser.ConfigParser()
config.read('./src/path.ini', 'UTF-8')
path_learningList = config.get('nn', 'path_learningList')
(x_train, t_train), (x_test, t_test) = encoding_load(path_learningList)

# 多次元になっているリストを2次元にならす
x_train = dl_flat2d(x_train)
t_train = dl_flat2d(t_train)
x_test = dl_flat2d(x_test)
t_test = dl_flat2d(t_test)
    
# ハイパーパラメータ
iters_num     = 3     # 計算式チェック回数

net = TwoLayerNet.TowLayerNet(x_train.shape[1], 40, t_train.shape[1])

for i in range(iters_num):

    # 学習データ取り出し
    batch_mask = np.random.choice(x_train.shape[0], 5)
    x = x_train[batch_mask]
    t = t_train[batch_mask]

    # print("x = ", x)
    # print("t = ", t)

    # 勾配計算
    grad_num = net.numerical_gradient(x, t)
    grad_bck = net.gradient(x, t)

    # 各勾配,バイアスの絶対誤差の平均
    for key in grad_num.keys():
        diff = np.average(np.abs(grad_bck[key] - grad_num[key]))
        print(key + " : " + str(diff))
