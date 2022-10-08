# 数値微分の結果と偏微分の結果との差分を確認する
# 差が大きい場合、誤差逆伝播計算式が誤っている可能性が高いことになる
# 理想は 1e-10 以内に納めること

import TwoLayerNet
import numpy as np
import pickle
import sys
import pathlib
    
# ハイパーパラメータ
iters_num     = 3     # 計算式チェック回数

# commonフォルダ内読み込みのため
deepLearning_dir = pathlib.Path(__file__).parent
src_dir = deepLearning_dir.parent
root_dir = src_dir.parent
dir_lst = [deepLearning_dir, src_dir, root_dir]
for dir_name in dir_lst:
    if str(dir_name) not in sys.path:
        sys.path.append(str(dir_name))

with open(str(root_dir) + "\\dst\\learningList\\t.pickle", 'rb') as f:
    tData = pickle.load(f)

with open(str(root_dir) + "\\dst\\learningList\\x.pickle", 'rb') as f:
    xData = pickle.load(f)

net = TwoLayerNet.TowLayerNet(131, 30, 24)

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
