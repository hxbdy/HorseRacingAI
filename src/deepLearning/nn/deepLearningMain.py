# NN学習本体
# 学習済みパラメータは dst\trainedParam\newest に保存する
# > python ./src/deepLearning/nn/deepLearningMain.py

import configparser
import TwoLayerNet
import time
import xross
np = xross.facttory_xp()
import shutil

from encoding_common import encoding_load, encoding_serial_dir_path, dl_copy2newest
from debug import stream_hdl, file_hdl

import logging
import configparser

# load config
config = configparser.ConfigParser()
config.read('./src/path.ini', 'UTF-8')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
# logger.addHandler(file_hdl("output"))

# 学習パラメータの保存先取得
path_root_trainedParam = config.get('nn', 'path_root_trainedParam')
serial_dir_path = encoding_serial_dir_path(path_root_trainedParam)

# 学習に使うエンコードを学習済みのパラメータを保存するフォルダにもコピーしておく
# newest学習データの読込
path_learningList = config.get('nn', 'path_learningList')
shutil.copytree(path_learningList, serial_dir_path + "learningList/")

x_train, t_train, x_test, t_test = encoding_load(path_learningList)

# ハイパーパラメータ
iters_num     = 50000
train_size    = x_train.shape[0]
batch_size    = 5     # 1度に学習するレース数

train_loss_list = []
train_acc_list = []
test_acc_list = []

# 確率的勾配降下法(SGD)
def grad_SGD(net, grad):
    learning_rate = 0.01
    for key in ('W1', 'b1', 'W2', 'b2'):
        net.params[key] -= learning_rate * grad[key]

# Momentum法
velocity = {}
def grad_Momentum(net, grad):
    global velocity
    momentum =  0.9
    learning_rate = 1
    if(len(velocity)==0):
        for key in ('W1', 'b1', 'W2', 'b2'):
            velocity[key] = np.zeros_like(net.params[key])
    for key in ('W1', 'b1', 'W2', 'b2'):
        velocity[key] = momentum * velocity[key] - learning_rate * grad[key]
        net.params[key] += velocity[key]

# AdaGrad法
d = {}
def grad_AdaGrad(net, grad):
    global d
    learning_rate = 0.01
    if(len(d)==0):
        for key in ('W1', 'b1', 'W2', 'b2'):
            d[key] = np.zeros_like(net.params[key])
    for key in ('W1', 'b1', 'W2', 'b2'):
        d[key] += grad[key] ** 2
        net.params[key] -= learning_rate * grad[key] / (np.sqrt(d[key]) + 1e-8)

# Adam法
mean = {}
variance = {}
def grad_Adam(net, grad):
    global mean
    global variance
    beta1 = 0.9
    beta2 = 0.999
    learning_rate = 1
    if(len(mean)==0):
        for key in ('W1', 'b1', 'W2', 'b2'):
            mean[key] = np.zeros_like(net.params[key])
    if(len(variance)==0):
        for key in ('W1', 'b1', 'W2', 'b2'):
            variance[key] = np.zeros_like(net.params[key])
    for key in ('W1', 'b1', 'W2', 'b2'):
        mean[key] = beta1 * mean[key] + (1 - beta1) * grad[key]
        variance[key] = beta2 * variance[key] + (1 - beta2) * grad[key] ** 2
        m = mean[key] / (1 - beta1)
        v = variance[key] / (1 - beta2)
        net.params[key] -= learning_rate * m / (np.sqrt(v) + 1e-8)

# 解析用に学習途中のデータを確認したいのでジェネレータ関数としている
# iter_per_epoch 毎に yeild する
def deep_learning_main():
    net = TwoLayerNet.TowLayerNet(x_train.shape[1], 40, t_train.shape[1])
    # 初期化時点のパラメータをセーブ
    net.seveParam(serial_dir_path + "init/")

    # iter_per_epoch = int(max(train_size / batch_size, 1))
    iter_per_epoch = 100
    for i in range(iters_num):

        # 学習データ取り出し
        batch_mask = np.random.choice(train_size, batch_size)
        x = x_train[batch_mask]
        t = t_train[batch_mask]

        # 勾配計算
        grad = net.gradient(x,t)

        # 確率的勾配降下法(SGD)
        grad_SGD(net, grad)

        # 教師tとの誤差確認
        loss = net.loss(x,t)
        train_loss_list.append(loss)

        if i % iter_per_epoch == 0:
            # 精度確認

            train_acc = net.accuracy(x_train, t_train).item()
            train_acc_list.append(train_acc)

            test_acc  = net.accuracy(x_test, t_test).item()
            test_acc_list.append(test_acc)

            logger.info("progress {0} / {1}".format(i, iters_num))
            logger.info("train_acc = {0:0.5f} | test_acc = {1:0.5f}".format(train_acc, test_acc))
            logger.info("========================================")

            yield net

    # 保存
    logger.info("Save param")
    net.seveParam(serial_dir_path)
    logger.info("Finish")
    logger.info("========================================")
    
    # 最新フォルダにも結果をコピー
    dl_copy2newest(serial_dir_path)

if __name__ == "__main__":
    time_sta = time.perf_counter()

    for i in deep_learning_main():
        pass
    
    time_end = time.perf_counter()

    logger.info("Learning Time = {0}".format(time_end - time_sta))
