# NN学習本体
# 学習したパラメータ, バイアスは ./dst/trainedParam/*.txt で確認可能
# 2020年までのデータで学習し, 2021年のレースで精度を確認している
# > python ./src/deepLearning/nn/deepLearningMain.py

import configparser
import TwoLayerNet
import numpy as np

from getFromDB import *
from encodingXClass import *
from table import *
from encoding_common import *

# 学習データの読込
config = configparser.ConfigParser()
config.read('./src/path.ini')
path_learningList = config.get('nn', 'path_learningList')
(x_train, t_train), (x_test, t_test) = encoding_load(path_learningList)

# 多次元になっているリストを2次元にならす
x_train = dl_flat2d(x_train)
t_train = dl_flat2d(t_train)
x_test = dl_flat2d(x_test)
t_test = dl_flat2d(t_test)

# ハイパーパラメータ
iters_num     = 30000
train_size    = x_train.shape[0]
learning_rate = 0.1   # 勾配更新単位
batch_size    = 5     # 1度に学習するレース数

train_loss_list = []
train_acc_list = []
test_acc_list = []

# 解析用に学習途中のデータを確認したいのでジェネレータ関数としている
# iter_per_epoch 毎に yeild する
def deep_learning_main():
    net = TwoLayerNet.TowLayerNet(x_train.shape[1], 40, t_train.shape[1])

    # iter_per_epoch = int(max(train_size / batch_size, 1))
    iter_per_epoch = 100
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

        if i % iter_per_epoch == 0:
            # 精度確認

            train_acc = net.accuracy(x_train, t_train)
            train_acc_list.append(train_acc)

            test_acc  = net.accuracy(x_test, t_test)
            test_acc_list.append(test_acc)

            logger.info("progress {0} / {1}".format(i, iters_num))
            logger.info("train_acc = {0:0.5f} | test_acc = {1:0.5f}".format(train_acc, test_acc))
            logger.info("========================================")

            yield net

    # 保存
    logger.info("Save param")
    net.seveParam()
    logger.info("Finish")
    logger.info("========================================")

if __name__ == "__main__":
    for i in deep_learning_main():
        None
