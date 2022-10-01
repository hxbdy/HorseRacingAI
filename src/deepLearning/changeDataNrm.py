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
from iteration_utilities import deepflatten

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

if __name__ == "__main__":

    # log出力ファイルのクリア
    with open(log_file_path, mode = 'w'):
        pass

    # X.pickle, t.pickle 読込
    with open(str(root_dir) + "\\dst\\learningList\\t.pickle", 'rb') as f:
        t_train = pickle.load(f)
    with open(str(root_dir) + "\\dst\\learningList\\X.pickle", 'rb') as f:
        x_train = pickle.load(f)

    # start_year <= data <= end_year のレースから limit 件取得する
    # 基となるデータを ./src/deepLearning/scrapingDataNrm.py を実行して生成した上で実行すること
    # MgrClass の生成条件 start_year, end_year, limit は統一すること
    totalList = MgrClass(start_year = 1800, end_year = 2020, XclassTbl = chgXTbl, tclassTbl = tTbl, limit = -1)
    totalList.set_totalList(x_train, t_train)

    x_train, t_train = totalList.getTotalList()

    # 書き込み
    logger.info("========================================")
    OUTPUT_PATH = str(root_dir) + "\\dst\\learningList\\"
    
    # 保存先フォルダの存在確認
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    fn = "X"
    logger.info("Save {0}{1}.pickle".format(OUTPUT_PATH, fn))
    with open(OUTPUT_PATH + fn + ".pickle", 'wb') as f:
        pickle.dump(x_train, f)

    fn = "t"
    logger.info("Save {0}{1}.pickle".format(OUTPUT_PATH, fn))
    with open(OUTPUT_PATH + fn + ".pickle", 'wb') as f:
        pickle.dump(t_train, f)
