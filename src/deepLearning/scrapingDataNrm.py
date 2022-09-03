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
from common.normalization import *
from common.padding import *
from common.getFromDB import *
from common.fix import *

# 学習データテーブルのインデックス定義
STRUCT_LIST = 0
STRUCT_GET  = 1
STRUCT_FIX  = 2
STRUCT_PAD  = 3
STRUCT_NRM  = 4

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


OUTPUT_PATH = str(root_dir) + "\\dst\\learningList\\"

"""pickleでデータを読み込み・保存"""
def read_data(read_file_name):
    """
    learningListフォルダ内にpicle化したファイルを読み込む。
    存在しない場合は文字列を返す．
    """
    try:
        with open(OUTPUT_PATH + read_file_name + ".pickle", "rb") as f:
            data = pickle.load(f)
    except FileNotFoundError:
        data = "FileNotFoundError"
    return data

def save_data(save_data, save_file_name):
    """
    learningListフォルダ内にpicle化したファイルを保存する。
    """
    with open(OUTPUT_PATH + save_file_name + ".pickle", 'wb') as f:
        pickle.dump(save_data, f)

if __name__ == "__main__":

    # 学習リスト作成
    totalXList = []
    totaltList = []

    # レース毎のデータ保管リスト
    marginList = []
    moneyList = []
    horseNumList = []
    courseDistanceList = []
    raceStartTimeList = []
    courseConditionList = []
    weatherList = []
    horseAgeList = []
    burdenWeightList = []
    postPositionList = []
    jockeyList = []
    cumPerformList = []

    # 一度のレースで出た馬の最大頭数
    maxHorseNum = 24

    # 総レース数取得
    totalRaceList = getTotalRaceList()
    totalRaceNum  = len(totalRaceList)

    # 進捗確認カウンタ
    comp_cnt = 1

    for race in totalRaceList:

        logger.info("========================================")
        logger.info("From netkeiba.db info =>")
        logger.info("https://db.netkeiba.com/race/{0}".format(race))
        logger.info("progress : {0} / {1}".format(comp_cnt, totalRaceNum))
        comp_cnt += 1

        # 取得するデータ一覧
        FlowTbl = [
            # 正解ラベルt
            [marginList         , getMarginList        , fixMarginList         , padMarginList         , nrmMarginList], 
            # 教師データX
            [moneyList          , getMoneyList         , fixMoneyList          , padMoneyNrm           , nrmMoney],
            [horseNumList       , getHorseNumList      , fixHorseNumList       , padHorseNumList       , nrmHorseNumList],
            [courseConditionList, getCourseCondition   , fixCourseConditionList, padCourseConditionList, nrmCourseCondition],
            [courseDistanceList , getCourseDistanceList, fixCourseDistanceList , padCourseDistanceList , nrmCourseDistanceList],
            [raceStartTimeList  , getRaceStartTimeList , fixRaceStartTimeList  , padRaceStartTimeList  , nrmRaceStartTime],
            [weatherList        , getWeather           , fixWeatherList        , padWeatherList        , nrmWeather],
            [horseAgeList       , getBirthDayList      , fixBirthDayList       , padHorseAgeList       , nrmHorseAge],
            [burdenWeightList   , getBurdenWeightList  , fixBurdenWeightList   , padBurdenWeightList   , nrmBurdenWeightAbs],
            [postPositionList   , getPostPositionList  , fixPostPositionList   , padPostPositionList   , nrmPostPosition],
            [jockeyList         , getJockeyIDList      , fixJockeyIDList       , padJockeyList         , nrmJockeyID],
            [cumPerformList     , getCumPerformList    , fixCumPerformList     , padCumPerformList     , nrmCumPerformList]
        ]

        # 学習リストクリア
        for tbl in FlowTbl:
            tbl[STRUCT_LIST].clear()

        # レース開催日取得
        d0 = getRaceDate(race)
        
        for func in FlowTbl:
            # 対象データをDBから取得
            args = []
            args.append((func[STRUCT_GET])(race))

            # 調整に必要なデータがあるならここで追加する
            if func[STRUCT_GET] == getBirthDayList:
                args.append(d0)

            # 要素を調整
            func[STRUCT_LIST] = (func[STRUCT_FIX])(args)

            # ダミーデータを挿入
            func[STRUCT_LIST] = (func[STRUCT_PAD])(func[STRUCT_LIST], maxHorseNum)

            # 標準化
            func[STRUCT_LIST] = (func[STRUCT_NRM])(func[STRUCT_LIST])

        # 各リスト確認
        logger.debug("========================================")
        logger.debug("t                   (len : {0}) = {1}".format(len(FlowTbl[0][STRUCT_LIST]) , FlowTbl[0][STRUCT_LIST]))
        logger.debug("moneyList           (len : {0}) = {1}".format(len(FlowTbl[1][STRUCT_LIST]) , FlowTbl[1][STRUCT_LIST]))
        logger.debug("horseNumList        (len : {0}) = {1}".format(len(FlowTbl[2][STRUCT_LIST]) , FlowTbl[2][STRUCT_LIST]))
        logger.debug("courseConditionList (len : {0}) = {1}".format(len(FlowTbl[3][STRUCT_LIST]) , FlowTbl[3][STRUCT_LIST]))
        logger.debug("courseDistanceList  (len : {0}) = {1}".format(len(FlowTbl[4][STRUCT_LIST]) , FlowTbl[4][STRUCT_LIST]))
        logger.debug("raceStartTimeList   (len : {0}) = {1}".format(len(FlowTbl[5][STRUCT_LIST]) , FlowTbl[5][STRUCT_LIST]))
        logger.debug("weatherList         (len : {0}) = {1}".format(len(FlowTbl[6][STRUCT_LIST]) , FlowTbl[6][STRUCT_LIST]))
        logger.debug("horseAgeList        (len : {0}) = {1}".format(len(FlowTbl[7][STRUCT_LIST]) , FlowTbl[7][STRUCT_LIST]))
        logger.debug("burdenWeightList    (len : {0}) = {1}".format(len(FlowTbl[8][STRUCT_LIST]) , FlowTbl[8][STRUCT_LIST]))
        logger.debug("postPositionList    (len : {0}) = {1}".format(len(FlowTbl[9][STRUCT_LIST]) , FlowTbl[9][STRUCT_LIST]))
        logger.debug("jockeyList          (len : {0}) = {1}".format(len(FlowTbl[10][STRUCT_LIST]), FlowTbl[10][STRUCT_LIST]))
        logger.debug("cumPerformList      (len : {0}) = {1}".format(len(FlowTbl[11][STRUCT_LIST]), FlowTbl[11][STRUCT_LIST]))

        # 教師リストのみ取り出し
        t = FlowTbl.pop(0)

        # FlowTbl の1列目(リスト)のみ取り出して一次元化
        learningList = [row[0] for row in FlowTbl]
        learningList = list(deepflatten(learningList))

        # 保存用リストに追加
        totalXList.append(learningList)
        totaltList.append(t)

    # 書き込み
    logger.info("========================================")
    
    # 保存先フォルダの存在確認
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    fn = "X"
    logger.info("Save {0}{1}.pickle".format(OUTPUT_PATH, fn))
    save_data(totalXList, fn)

    fn = "t"
    logger.info("Save {0}{1}.pickle".format(OUTPUT_PATH, fn))
    save_data(totaltList, fn)
