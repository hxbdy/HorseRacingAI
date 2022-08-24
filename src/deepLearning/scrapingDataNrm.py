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

loc_list = ['札幌', '函館', '福島', '新潟', '東京', '中山', '中京', '京都', '阪神', '小倉']

# 学習データテーブルのインデックス定義
STRUCT_LIST = 0
STRUCT_GET  = 1
STRUCT_FIX  = 2
STRUCT_PAD  = 3
STRUCT_NRM  = 4

## 馬の強さを計算
def getStandardTime(distance, condition, track, location):
    # レースコースの状態に依存する基準タイム(秒)を計算して返す
    # performancePredictionで予測した係数・定数を下の辞書の値に入れる．
    # loc_dictのOtherは中央競馬10か所以外の場合の値．10か所の平均値を取って作成する．
    dis_coef = 0.066433
    intercept = -9.6875
    cond_dict = {'良':-0.3145, '稍重':0.1566, '重':0.1802, '不良':-0.0223}
    track_dict = {'芝':-1.2514, 'ダ': 1.2514}
    loc_dict = {'札幌':1.1699, '函館':0.3113, '福島':-0.3205, '新潟':-0.2800, '東京':-0.8914,\
         '中山':0.2234, '中京':0.1815, '京都':-0.1556, '阪神':-0.4378, '小倉':0.1994, 'Other':0}
    
    std_time = dis_coef*distance + cond_dict[condition] + track_dict[track] + loc_dict[location] + intercept
    return std_time

def getPerformance(standard_time, goal_time, weight, grade):
    # 走破タイム・斤量などを考慮し，「強さ(performance)」を計算
    # 以下のeffectの値，計算式は適当
    weight_effect = 1+ (55 - weight)/1000
    grade_effect_dict = {'G1':1.14, 'G2':1.12, 'G3':1.10, 'OP':1.0, 'J.G1':1.0, 'J.G2':1.0, 'J.G3':1.0}
    perform = (10 + standard_time - goal_time*weight_effect) * grade_effect_dict[grade]
    return perform

# 累計値の計算
# ToDo : mainで一度呼ぶ。結果をXに追加する
def calCumPerformance(horsedb):
    # 各レースの結果から強さ(performance)を計算し，その最大値を記録していく
    # (外れ値を除くために，2番目の強さでもいいかもしれない．)
    rgdb = read_data("raceGradedb")

    horsedb.cum_perform = []
    for horse_idx in range(len(horsedb.perform_contents)):
        horse_perform = horsedb.perform_contents[horse_idx] 
        max_performance_list = []
        max_performance = -1000.0
        horse_perform.reverse()
        for race_idx in range(len(horse_perform)):
            race_result = horse_perform[race_idx]
            # ゴールタイムを取得
            goaltime = race_result[10]
            try:
                goaltime_sec = float(goaltime.split(':')[0])*60 + float(goaltime.split(':')[1])
            except:
                goaltime_sec = 240
            # 斤量を取得
            try:
                burden_weight = float(race_result[9])
            except:
                burden_weight = 40
            # 馬場状態と競馬場を取得
            condition = horsedb.getCourseCondition(horse_idx, race_result[2])
            location = horsedb.getCourseLocation(horse_idx, race_result[2])
            if location not in loc_list:
                location = "Other"
            # 芝かダートか
            if race_result[11][0] == "芝":
                track = "芝"
            elif race_result[11][0] == "ダ":
                track = "ダ"
            else:
                track = "E"
            # コースの距離
            dis_str = race_result[11]
            try:
                distance = float(re.sub(r'\D', '', dis_str).replace(" ", ""))
            except:
                distance = "E"
            # レースのグレード (G1,G2,G3,OP)
            # 日本の中央競馬以外のレースは全てOP扱いになる
            try:
                raceid = race_result[2]
                race_year = int(race_result[0][0:4])
                grade = "OP"
                for i in range(len(rgdb.raceID_list)):
                    if race_year != int(rgdb.raceID_list_year[i]):
                        continue
                    if raceid in rgdb.raceID_list[i]:
                        grade = "G" + rgdb.raceID_list_grade[i]
            except:
                grade = "E"
                

            # 計算不能な場合を除いてperformanceを計算
            if track != "E" and distance != "E" and grade != "E":
                standard_time = horsedb.getStandardTime(distance, condition, track, location)
                performance = horsedb.getPerformance(standard_time, goaltime_sec, burden_weight, grade)

            if performance > max_performance:
                max_performance = performance
            max_performance_list.append(max_performance)
        max_performance_list.reverse()
        horsedb.cum_perform.append(max_performance_list)

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

    # 一度のレースで出た馬の最大頭数
    maxHorseNum = 24

    # 総レース数取得
    totalRaceList = getTotalRaceList()
    totalRaceNum  = len(getTotalRaceList())

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
            [jockeyList         , getJockeyIDList      , fixJockeyIDList       , padJockeyList         , nrmJockeyID]
        ]

        # 学習リストクリア
        for tbl in FlowTbl:
            tbl[STRUCT_LIST].clear()

        # レース開催日取得
        d0 = getRaceDateList(race)
        
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
