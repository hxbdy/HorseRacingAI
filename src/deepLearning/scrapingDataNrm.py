# AI 学習用データの作成
# DB からデータを標準化し、学習データX と 教師データt の対となるリストを作成する
# 出力先 ./dst/learningList/X.pickle, t.pickle

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

if __name__ == "__main__":

    # 入力用テーブル
    XTbl = [
        HorseNumClass,
        CourseConditionClass,
        CourseDistanceClass,
        RaceStartTimeClass,
        WeatherClass,
        HorseAgeClass,
        BurdenWeightClass,
        PostPositionClass,
        JockeyClass,
        CumPerformClass
    ]

    # 正解用テーブル
    tTbl = [
        MarginClass
    ]

    # <= year のレースから取得する
    year = 1986
    totalList = MgrClass(year, XTbl, tTbl)
    train_x, train_t = totalList.getTotalList()

    # 書き込み
    logger.info("========================================")
    OUTPUT_PATH = str(root_dir) + "\\dst\\learningList\\"
    
    # 保存先フォルダの存在確認
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    fn = "X"
    logger.info("Save {0}{1}.pickle".format(OUTPUT_PATH, fn))
    with open(OUTPUT_PATH + fn + ".pickle", 'wb') as f:
        pickle.dump(train_x, f)

    fn = "t"
    logger.info("Save {0}{1}.pickle".format(OUTPUT_PATH, fn))
    with open(OUTPUT_PATH + fn + ".pickle", 'wb') as f:
        pickle.dump(train_t, f)
