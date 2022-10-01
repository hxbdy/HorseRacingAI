# AI 学習用データの作成
# すでに生成済みの学習データX と 教師データtの一部データを差し替えるためのコード
# 対象のみを DB から標準化し、学習データX と 教師データt の対となるリストを作成する
# 読込及び出力先 ./dst/learningList/X.pickle, t.pickle
# > python ./src/deepLearning/changeDataNrm.py

import pickle
import sys
import os
import pathlib
import logging
import re

# commonフォルダ内読み込みのため
deepLearning_dir = pathlib.Path(__file__).parent
src_dir = deepLearning_dir.parent
root_dir = src_dir.parent
dir_lst = [deepLearning_dir, src_dir, root_dir]
for dir_name in dir_lst:
    if str(dir_name) not in sys.path:
        sys.path.append(str(dir_name))

import common.debug
from common.getFromDB import *
from common.XClass import *

# 学習テーブル, 教師テーブル取得
from table import XTbl
from table import tTbl
from table import chgXTbl
from table import chgtTbl

def save_nn_data(pkl_name, data):
    OUTPUT_PATH = str(root_dir) + "\\dst\\learningList\\"
    
    # 保存先フォルダの存在確認
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    logger.info("Save {0}{1}".format(OUTPUT_PATH, pkl_name))
    with open(OUTPUT_PATH + pkl_name, 'wb') as f:
        pickle.dump(data, f)

if __name__ == "__main__":

    # log出力ファイルのクリア
    with open(log_file_path, mode = 'w'):
        pass

    # X.pickle, t.pickle 読込
    with open(str(root_dir) + "\\dst\\learningList\\t_1800-2020.pickle", 'rb') as f:
        t_train = pickle.load(f)
    with open(str(root_dir) + "\\dst\\learningList\\X_1800-2020.pickle", 'rb') as f:
        x_train = pickle.load(f)
    with open(str(root_dir) + "\\dst\\learningList\\t_2021-2021.pickle", 'rb') as f:
        t_test = pickle.load(f)
    with open(str(root_dir) + "\\dst\\learningList\\X_2021-2021.pickle", 'rb') as f:
        x_test = pickle.load(f)

    # start_year <= data <= end_year のレースから limit 件取得する
    # 基となるデータを ./src/deepLearning/scrapingDataNrm.py を実行して生成した上で実行すること
    # MgrClass の生成条件 start_year, end_year, limit は統一すること
    # XclassTbl を chgXTbl に差し替え
    
    # 学習用データ
    logger.info("========================================")
    logger.info("generate train data")
    start_year_train = 1800
    end_year_train   = 2020
    total_train_list = MgrClass(start_year = start_year_train, end_year = end_year_train, XclassTbl = chgXTbl, tclassTbl = tTbl, limit = -1)
    total_train_list.set_totalList(x_train, t_train)
    x_train, t_train, odds_train = total_train_list.getTotalList()

    # 学習確認用テストデータ
    logger.info("========================================")
    logger.info("generate test data")
    start_year_test = 2021
    end_year_test   = 2021
    total_test_list = MgrClass(start_year = start_year_train, end_year = end_year_train, XclassTbl = chgXTbl, tclassTbl = tTbl, limit = -1)
    total_train_list.set_totalList(x_test, t_test)
    x_test, t_test, odds_test = total_test_list.getTotalList()

    # 書き込み
    logger.info("========================================")

    save_nn_data("X_{0}-{1}.pickle".format(start_year_train, end_year_train), x_train)
    save_nn_data("t_{0}-{1}.pickle".format(start_year_train, end_year_train), t_train)
    save_nn_data("odds_{0}-{1}.pickle".format(start_year_train, end_year_train), odds_train)

    save_nn_data("X_{0}-{1}.pickle".format(start_year_test, end_year_test), x_test)
    save_nn_data("t_{0}-{1}.pickle".format(start_year_test, end_year_test), t_test)
    save_nn_data("odds_{0}-{1}.pickle".format(start_year_test, end_year_test), odds_test)
