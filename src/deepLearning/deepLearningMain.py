import TwoLayerNet
import numpy as np
import pickle
import sys
import pathlib

# ハイパーパラメータ
iters_num    = 1000000
lerning_rate = 0.1  # 勾配更新単位
batch_size   = 1     # 1度に学習するレース数

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

net = TwoLayerNet.TowLayerNet(131,50,24)

loss = []

for i in range(iters_num):

    # 学習データ取り出し
    batch = np.random.randint(0, 4326)
    
    x = np.array(xData[batch])
    x = x.reshape([1, -1])

    t = np.array(tData[batch])

    # 勾配計算
    grad = net.gradient(x,t)
    net.params['W1'] -= lerning_rate * grad['W1']
    net.params['b1'] -= lerning_rate * grad['b1']
    net.params['W2'] -= lerning_rate * grad['W2']
    net.params['b2'] -= lerning_rate * grad['b2']
    
    # 教師tとの誤差確認
    l = net.loss(x,t)
    loss.append(l)

    # print progress bar
    per = int(i / iters_num * 20)
    pro_bar = ('=' * per) + (' ' * (20 - per))
    print('\r[{0}] {1:02.03}% err={2}'.format(pro_bar, i / iters_num * 100, l), end='')

# 保存
net.saveLoss(loss)
net.seveParam()
