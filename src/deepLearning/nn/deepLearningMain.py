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
    with open(path_learningList + analysis_train_file_name, 'rb') as f:
        analysis_train = np.array(pickle.load(f))

    x_test = load_flat_pcikle(X_test_file_name)
    t_test = load_flat_pcikle(t_test_file_name)
    with open(path_learningList + analysis_test_file_name, 'rb') as f:
        analysis_test = np.array(pickle.load(f))

    return (x_train, t_train, analysis_train), (x_test, t_test, analysis_test)

# 学習データの読込
(x_train, t_train, analysis_train), (x_test, t_test, analysis_test) = load_horse_racing_data()

# ハイパーパラメータ
iters_num     = 30000
train_size    = x_train.shape[0]
learning_rate = 0.1   # 勾配更新単位
batch_size    = 5     # 1度に学習するレース数

# 解析用パラメータ
# g1-g3レース数


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

        # 解析データ取り出し
        # オッズ取り出し
        analysis_train_odds = analysis_train[:, [True, False]]
        analysis_train_odds = analysis_train_odds.reshape(1, -1)
        analysis_train_odds = analysis_train_odds[0]

        analysis_test_odds = analysis_test[:, [True, False]]
        analysis_test_odds = analysis_test_odds.reshape(1, -1)
        analysis_test_odds = analysis_test_odds[0]

        # グレード取り出し
        analysis_train_grade = analysis_train[:, [False, True]]
        analysis_train_grade = analysis_train_grade.reshape(1, -1)
        analysis_train_grade = analysis_train_grade[0]
        TRAIN_G1_RACE_NUM = np.count_nonzero(analysis_train_grade == 1)
        TRAIN_G2_RACE_NUM = np.count_nonzero(analysis_train_grade == 2)
        TRAIN_G3_RACE_NUM = np.count_nonzero(analysis_train_grade == 3)

        analysis_test_grade = analysis_test[:, [False, True]]
        analysis_test_grade = analysis_test_grade.reshape(1, -1)
        analysis_test_grade = analysis_test_grade[0]
        TEST_G1_RACE_NUM = np.count_nonzero(analysis_test_grade == 1)
        TEST_G2_RACE_NUM = np.count_nonzero(analysis_test_grade == 2)
        TEST_G3_RACE_NUM = np.count_nonzero(analysis_test_grade == 3)

        train_pay, (train_g1, train_g2, train_g3) = net.hit(x_train, t_train, analysis_train_odds, wallet_train, bet_train, analysis_train_grade)
        test_pay, (test_g1, test_g2, test_g3)  = net.hit(x_test, t_test, analysis_test_odds, wallet_test, bet_test, analysis_test_grade)

        # 学習データで推論結果, 学習データでいくら儲けたか, テストデータで推論結果, テストデータでいくら儲けたか
        logger.info("train_acc = {0:0.5f} | train_pay = {1:8.0f} | (g1, g2, g3) = {2:1.3f}, {3:1.3f}, {4:1.3f}".format(train_acc, train_pay, 1.0 * train_g1 / TRAIN_G1_RACE_NUM, 1.0 * train_g2 / TRAIN_G2_RACE_NUM, 1.0 * train_g3 / TRAIN_G3_RACE_NUM))
        logger.info("test_acc  = {0:0.5f} | test_pay  = {1:8.0f} | (g1, g2, g3) = {2:1.3f}, {3:1.3f}, {4:1.3f}".format(test_acc, test_pay, 1.0 * test_g1 / TEST_G1_RACE_NUM, 1.0 * test_g2 / TEST_G2_RACE_NUM, 1.0 * test_g3 / TEST_G3_RACE_NUM))
        logger.info("===============================================================================")

# 保存
net.saveLoss(train_loss_list)
net.seveParam()
