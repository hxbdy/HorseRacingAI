import TwoLayerNet
import numpy as np

# ハイパーパラメータ
iters_num    = 50000
lerning_rate = 0.01  # 勾配更新単位
batch_size   = 1     # 1度に学習するレース数

# ダミー教師t生成
# 合計で必ず1にする必要がある(偏微分の導出に影響する)
t_data_dummy = np.array([0.5, 0.3, 0.1, 0.05, 0.03, 0.01, 0.005, 0.003, 0.001, 0.001])


net = TwoLayerNet.TowLayerNet(160,3000,10)

x    = []
t    = []
loss = []

for i in range(iters_num):

    # ダミー入力X 生成
    x_data_dummy = np.random.rand(1, 160)
    x = x_data_dummy

    t = t_data_dummy

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
