# NN学習を呼び出す。学習途中の情報を使ってグラフを描画したりもする
# > python ./src/deepLearning/analysis/learning_check.py

import numpy as np
import pickle
import os

from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from matplotlib import pyplot as plt

from file_path_mgr import path_ini
from table import analysis_train_file_name, analysis_test_file_name
from deepLearningMain import *

# load config
path_root_trainedParam = path_ini('nn', 'path_root_trainedParam')
path_learningList      = path_ini('nn', 'path_learningList')
path_graph             = path_ini('nn', 'path_graph')

def get_analysis_info(analysis_data, mask):
    # 解析データ取り出し
    analysis_col = analysis_data[:, mask]
    analysis_col = analysis_col.reshape(1, -1)
    analysis_col = analysis_col[0]
    return analysis_col

# ペイ確認
bet_train = 100
bet_test = 100

# =========== 1学習ごとのリスト ===========
train_wallet_list = []
test_wallet_list = []

# グレードごとの勝率確認
train_g1_list = []
test_g1_list = []

train_g2_list = []
test_g2_list = []

train_g3_list = []
test_g3_list = []
# ========================================
# ========= 学習平均確認のリスト ===========
train_wallet_ave_list = []
test_wallet_ave_list = []

# グレードごとの勝率確認
train_g1_ave_list = []
test_g1_ave_list = []

train_g2_ave_list = []
test_g2_ave_list = []

train_g3_ave_list = []
test_g3_ave_list = []
# ========================================

# 解析用情報読込
# info = [[odds, grade]]
with open(path_learningList + analysis_train_file_name, 'rb') as f:
        analysis_train = np.array(pickle.load(f))

with open(path_learningList + analysis_test_file_name, 'rb') as f:
        analysis_test = np.array(pickle.load(f))

def learning_check():

    # ./src/deepLearning/nn/deepLearningMain.py/deep_learning_main()
    # iter_per_epoch 毎に返ってくる
    for net in deep_learning_main():

        # 解析データ取り出し
        # オッズ取り出し
        analysis_train_odds = get_analysis_info(analysis_train, [True, False])
        analysis_test_odds  = get_analysis_info(analysis_test, [True, False])

        # グレード取り出し
        analysis_train_grade = get_analysis_info(analysis_train, [False, True])
        TRAIN_G1_RACE_NUM = np.count_nonzero(analysis_train_grade == 1)
        TRAIN_G2_RACE_NUM = np.count_nonzero(analysis_train_grade == 2)
        TRAIN_G3_RACE_NUM = np.count_nonzero(analysis_train_grade == 3)

        analysis_test_grade = get_analysis_info(analysis_test, [False, True])
        TEST_G1_RACE_NUM = np.count_nonzero(analysis_test_grade == 1)
        TEST_G2_RACE_NUM = np.count_nonzero(analysis_test_grade == 2)
        TEST_G3_RACE_NUM = np.count_nonzero(analysis_test_grade == 3)

        train_pay, (train_g1, train_g2, train_g3) = net.hit(x_train, t_train, analysis_train_odds, bet_train, analysis_train_grade)
        train_wallet_list.append(train_pay / (x_train.shape[0] * bet_train)) # 1レース平均回収額

        test_pay, (test_g1, test_g2, test_g3)  = net.hit(x_test, t_test, analysis_test_odds, bet_test, analysis_test_grade)
        test_wallet_list.append(test_pay / (x_test.shape[0] * bet_test)) # 1レース平均回収額

        train_g1_list.append(1.0 * train_g1 / TRAIN_G1_RACE_NUM)
        train_g2_list.append(1.0 * train_g2 / TRAIN_G2_RACE_NUM)
        train_g3_list.append(1.0 * train_g3 / TRAIN_G3_RACE_NUM)

        test_g1_list.append(1.0 * test_g1 / TEST_G1_RACE_NUM)
        test_g2_list.append(1.0 * test_g2 / TEST_G2_RACE_NUM)
        test_g3_list.append(1.0 * test_g3 / TEST_G3_RACE_NUM)

        logger.info("  train (g1, g2, g3) = {0:1.3f}, {1:1.3f}, {2:1.3f} | pay = {3:7}".format(train_g1_list[-1], train_g2_list[-1], train_g3_list[-1], int(train_pay)))
        logger.info("  test  (g1, g2, g3) = {0:1.3f}, {1:1.3f}, {2:1.3f} | pay = {3:7}".format(test_g1_list[-1], test_g2_list[-1], test_g3_list[-1], int(test_pay)))
        logger.info("========================================")

if __name__ == "__main__":

    SAMPLING_NUM = 10
    for i in range(SAMPLING_NUM):
        logger.info("avaraging {0} / {1}".format(i, SAMPLING_NUM))

        train_wallet_list.clear()
        test_wallet_list.clear()
        train_g1_list.clear()
        test_g1_list.clear()
        train_g2_list.clear()
        test_g2_list.clear()
        train_g3_list.clear()
        test_g3_list.clear()

        learning_check()

        train_wallet_ave_list.append(train_wallet_list)
        test_wallet_ave_list.append(test_wallet_list)
        train_g1_ave_list.append(train_g1_list)
        test_g1_ave_list.append(test_g1_list)
        train_g2_ave_list.append(train_g2_list)
        test_g2_ave_list.append(test_g2_list)
        train_g3_ave_list.append(train_g3_list)
        test_g3_ave_list.append(test_g3_list)

    train_wallet_ave_list = np.average(train_wallet_ave_list, axis=0)
    test_wallet_ave_list  = np.average(test_wallet_ave_list, axis=0)
    train_g1_ave_list     = np.average(train_g1_ave_list, axis=0)
    test_g1_ave_list      = np.average(test_g1_ave_list, axis=0)
    train_g2_ave_list     = np.average(train_g2_ave_list, axis=0)
    test_g2_ave_list      = np.average(test_g2_ave_list, axis=0)
    train_g3_ave_list     = np.average(train_g3_ave_list, axis=0)
    test_g3_ave_list      = np.average(test_g3_ave_list, axis=0)

    # グラフ保存用フォルダ
    os.makedirs(path_graph, exist_ok=True)

    # グレード別正答率
    title = "AVE_ACC_G1"
    plt.figure() # 新規ウインドウ
    plt.title(title)
    plt.plot(train_g1_ave_list, label="train")
    plt.plot(test_g1_ave_list, label="test")
    plt.plot(train_g1_ave_list - test_g1_ave_list, label="train - test")
    plt.legend() # 凡例表示(labelで指定したテキストの表示)
    plt.savefig(path_graph + title + ".png")

    title = "AVE_ACC_G2"
    plt.figure() # 新規ウインドウ
    plt.title(title)
    plt.plot(train_g2_ave_list, label="train")
    plt.plot(test_g2_ave_list, label="test")
    plt.plot(train_g2_ave_list - test_g2_ave_list, label="train - test")
    plt.legend() # 凡例表示(labelで指定したテキストの表示)
    plt.savefig(path_graph + title + ".png")

    title = "AVE_ACC_G3"
    plt.figure() # 新規ウインドウ
    plt.title(title)
    plt.plot(train_g3_ave_list, label="train")
    plt.plot(test_g3_ave_list, label="test")
    plt.plot(train_g3_ave_list - test_g3_ave_list, label="train - test")
    plt.legend() # 凡例表示(labelで指定したテキストの表示)
    plt.savefig(path_graph + title + ".png")

    title = "AVE_Wallet"
    plt.figure() # 新規ウインドウ
    plt.title(title)
    plt.plot(train_wallet_ave_list, label="train")
    plt.plot(test_wallet_ave_list, label="test")
    plt.plot(train_wallet_ave_list - test_wallet_ave_list, label="train - test")
    plt.legend() # 凡例表示(labelで指定したテキストの表示)
    plt.savefig(path_graph + title + ".png")

    logger.info("display graph")
    plt.show()
