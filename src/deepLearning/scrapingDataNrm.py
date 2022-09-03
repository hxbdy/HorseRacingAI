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

def calCumNumOfWin(horsedb):
    # 累計勝利数を計算
    horsedb.cum_num_wins = []
    for horse_perform in horsedb.perform_contents:
        cum_win_list = []
        cum_win = 0
        horse_perform.reverse()
        for race_result in horse_perform:
            if race_result[8] == '1':
                cum_win += 1
            cum_win_list.append(cum_win)
        cum_win_list.reverse()
        horsedb.cum_num_wins.append(cum_win_list)

def calCumMoney(horsedb):
    # 累計獲得賞金を計算
    horsedb.cum_money = []
    for horse_perform in horsedb.perform_contents:
        cum_money_list = []
        cum_money = 0.0
        horse_perform.reverse()
        for race_result in horse_perform:
            if race_result[15] == ' ':
                money = 0.0
            else:
                money = float(race_result[15].replace(",",""))
            cum_money += money
            cum_money_list.append(cum_money)
        cum_money_list.reverse()
        horsedb.cum_money.append(cum_money_list)

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
