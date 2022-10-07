# NN学習本体
# 学習したパラメータ, バイアスは ./dst/trainedParam/*.txt で確認可能
# 2020年までのデータで学習し, 2021年のレースで精度を確認している
# > python ./src/deepLearning/nn/deepLearningMain.py

import configparser
import TwoLayerNet
import numpy as np
import pickle
import itertools

from getFromDB import *
from XClass import *
from table import *

# load config
config = configparser.ConfigParser()
config.read('./src/path.ini')
path_learningList = config.get('nn', 'path_learningList')

# pickle 読込
# numpy array に変換して返す
def load_flat_pcikle(pkl_name):
    with open(path_learningList + pkl_name, 'rb') as f:
        flat_pkl = []
        flat_pkl_list = pickle.load(f)
        for i in flat_pkl_list:
            flat_pkl.append(list(itertools.chain.from_iterable(i)))
        flat_pkl = np.array(flat_pkl)
        return flat_pkl

def load_horse_racing_data():
    x_train = load_flat_pcikle(X_train_file_name)
    t_train = load_flat_pcikle(t_train_file_name)
    with open(path_learningList + odds_train_file_name, 'rb') as f:
        odds_train = pickle.load(f)

    x_test = load_flat_pcikle(X_test_file_name)
    t_test = load_flat_pcikle(t_test_file_name)
    with open(path_learningList + odds_test_file_name, 'rb') as f:
        odds_test = pickle.load(f)

    return (x_train, t_train, odds_train), (x_test, t_test, odds_test)

# 学習データの読込
(x_train, t_train, odds_train), (x_test, t_test, odds_test) = load_horse_racing_data()

# ハイパーパラメータ
iters_num     = 30000
train_size    = x_train.shape[0]
learning_rate = 0.1   # 勾配更新単位
batch_size    = 5     # 1度に学習するレース数

# ペイ確認
wallet_train = 0
bet_train = 100

wallet_test = 0
bet_test = 100

net = TwoLayerNet.TowLayerNet(155, 40, 24)

train_loss_list = []
train_acc_list = []
test_acc_list = []

iter_per_epoch = int(max(train_size / batch_size, 1))
for i in range(iters_num):

    # 学習データ取り出し
    batch_mask = np.random.choice(train_size, batch_size)
    x = x_train[batch_mask]
    t = t_train[batch_mask]

    # 勾配計算
    grad = net.gradient(x,t)
    for key in ('W1', 'b1', 'W2', 'b2'):
        net.params[key] -= learning_rate * grad[key]
    
    # 教師tとの誤差確認
    loss = net.loss(x,t)
    train_loss_list.append(loss)

    if i % 100 == 0:
        train_acc = net.accuracy(x_train, t_train)
        test_acc  = net.accuracy(x_test, t_test)

        train_pay = net.hit(x_train, t_train, odds_train, wallet_train, bet_train)
        test_pay  = net.hit(x_test, t_test, odds_test, wallet_test, bet_test)

        # 学習データで推論結果, 学習データでいくら儲けたか, テストデータで推論結果, テストデータでいくら儲けたか
        logger.info("train_acc = {0:0.5f} | train_pay = {1:.0f}".format(train_acc, train_pay))
        logger.info("test_acc  = {0:0.5f} | test_pay  = {1:.0f}".format(test_acc, test_pay))
        logger.info("=============================================")

# 保存
net.saveLoss(train_loss_list)
net.seveParam()
