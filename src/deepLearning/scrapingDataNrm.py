import pickle
import sys
import os
import pathlib
import logging
import re
from datetime import date
from dateutil.relativedelta import relativedelta
import numpy as np
from iteration_utilities import deepflatten

# commonフォルダ内読み込みのため
deepLearning_dir = pathlib.Path(__file__).parent
src_dir = deepLearning_dir.parent
root_dir = src_dir.parent
dir_lst = [deepLearning_dir, src_dir, root_dir]
for dir_name in dir_lst:
    if str(dir_name) not in sys.path:
        sys.path.append(str(dir_name))

from common.RaceDB import RaceDB
from common.RaceGradeDB import RaceGradeDB
from common.normalization import *
from common.padding import *

loc_list = ['札幌', '函館', '福島', '新潟', '東京', '中山', '中京', '京都', '阪神', '小倉']

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
    # debug initialize
    # LEVEL : DEBUG < INFO < WARNING < ERROR < CRITICAL
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s [%(levelname)s] %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    #logging.disable(logging.DEBUG)

    # pickle読み込み
    logger.info("Database loading")

    # レース情報読み込み
    with open(str(root_dir) + "\\dst\\scrapingResult\\racedb.pickle", 'rb') as f:
            racedb = pickle.load(f)

    # 馬情報読み込み
    with open(str(root_dir) + "\\dst\\scrapingResult\\horsedb.pickle", 'rb') as f:
            horsedb = pickle.load(f)

    # G1-3情報読み込み
    # with open(str(root_dir) + "\\dst\\scrapingResult\\raceGradedb.pickle", 'rb') as f:
        #gradedb = pickle.load(f)

    logger.info("Database loading complete")

    # DBに一度のレースで出た馬の最大頭数を問い合わせる
    maxHorseNum = racedb.getMaxHorseNumLargestEver()
    
    totalXList = []
    totaltList = []
    totalRaceNum = len(racedb.raceID)

    for race in range(len(racedb.raceID)):

        logger.info("========================================")
        logger.info("From RaceDB info =>")
        logger.info("https://db.netkeiba.com/race/{0}".format(racedb.raceID[race]))
        logger.info("Generating input data : {0}/{1}".format(race+1, totalRaceNum))

        ## 正解ラベルの作成
        """
        # タイム取得
        # 標準化 -> ダミーデータ挿入
        goalTimeRowList = racedb.goalTimeConv2SecList(race)
        goalTimeNrmList = nrmGoalTime(goalTimeRowList)
        goalTimeExpList = padGoalTimeNrm(goalTimeNrmList, maxHorseNum)
        racedbLearningList.append(nrmGoalTime(goalTimeExpList))
        """
        # 着差取得
        # ダミーデータ挿入 -> 標準化
        # これを教師データtとする
        marginList = racedb.getMarginList(race)
        marginExpList = padMarginList(marginList, maxHorseNum)
        teachList = nrmMarginList(marginExpList)

        ## 学習リスト作成 (レースデータ)
        racedbLearningList = []

        # 天気取得
        # onehot表現 5列使用
        # (わりとどうでもよい変数だと思うので，1変数に圧縮してもよいと思う)
        for i in nrmWeather(racedb.getWeather(race)):
            racedbLearningList.append(i)

        # コース状態取得
        # onehot表現 3列使用
        # (1変数にしやすい変数であるが，onehotにして重みは学習に任せた方が良いと思う)
        for i in nrmCourseCondition(racedb.getCourseCondition(race)):
            racedbLearningList.append(i)

        # 出走時刻取得
        racedbLearningList.append(nrmRaceStartTime(racedb.getRaceStartTime(race)))

        # 距離取得
        # 最長距離で割って標準化
        MAX_DISTANCE = 3600
        distance = float(racedb.getCourseDistance(race))
        racedbLearningList.append(distance / MAX_DISTANCE)

        # 頭数取得
        # 最大の出馬数で割って標準化
        horseNum = float(racedb.getHorseNum(race))
        racedbLearningList.append(horseNum / maxHorseNum)

        # 賞金取得
        # ダミーデータ挿入 -> 標準化
        moneyList = racedb.getMoneyList(race)
        moneyExpList = padMoneyNrm(moneyList, maxHorseNum)
        racedbLearningList.append(nrmMoney(moneyExpList))

        # 賞金取得 その2 : 全レースの最高金額で割って正規化
        # ToDo : 最高金額を取得して割る作業を追加
        #racedbLearningList.append(racedb.getMoneyList2(race))
        
        logger.debug("[Weather, CourseCondition, RaceStartTime, CourseDistance, HorseNum, [Money]]")
        logger.debug(racedbLearningList)

        ## 学習リスト作成 (各馬のデータ)
        # レース開催日取得
        d0 = racedb.getRaceDate(race)

        # === horsedb問い合わせ ===
        horseAgeList = []
        burdenWeightList = []
        postPositionList = []
        jockeyList = []
        for horseID in racedb.horseIDs_race[race]:
            logger.debug("========================================")
            logger.debug("From HorseDB info =>")
            
            # horsedb へ horseID の情報は何番目に格納しているかを問い合わせる
            # 以降horsedbへの問い合わせは index を使う
            index = horsedb.getHorseInfo(horseID)
            logger.debug("https://db.netkeiba.com/horse/{0} => index : {1}".format(horseID, index))
            
            # 生涯獲得金取得
            # race時点での獲得賞金を取得
            # horsedb.getTotalEarned(index)

            # 通算成績取得[1st,2nd,3rd]
            # race開催時点での獲得賞金を取得
            # horsedb.getTotalWLRatio(index)

            # 出走当時の年齢取得(d0 > d1)
            d1 = horsedb.getBirthDay(index)
            age = horsedb.ageConv2Day(d0, d1)
            horseAgeList.append(age)

            # 斤量取得
            burdenWeight = horsedb.getBurdenWeight(index, racedb.raceID[race])
            burdenWeightList.append(burdenWeight)

            # 枠番取得
            postPosition = horsedb.getPostPosition(index, racedb.raceID[race])
            postPositionList.append(postPosition)

            # 騎手取得
            jockeyID = horsedb.getJockeyID(index, racedb.raceID[race])
            cntJockey = horsedb.countJockeyAppear(jockeyID)
            jockeyList.append(cntJockey)

            logger.debug("[HorseAge, BurdenWeight, PostPosition, JockeyID]")
            logger.debug("[{0}, {1}, {2}, {3}]".format(horseAgeList[-1], burdenWeightList[-1], postPositionList[-1], jockeyList[-1]))

        STRUCT_LIST = 0
        STRUCT_PAD  = 1
        STRUCT_NRM  = 2
        PadNrmStruct = [
            [horseAgeList    , padHorseAgeList    , nrmHorseAge],
            [burdenWeightList, padBurdenWeightList, nrmBurdenWeightAbs],
            [postPositionList, padPostPositionList, nrmPostPosition],
            [jockeyList      , padJockeyList      , nrmJockeyID]
        ]

        # 各リストにダミーデータを挿入
        logger.debug("========================================")
        logger.debug("padding and normalize start")
        for func in PadNrmStruct:
            # ダミーデータを挿入
            func[STRUCT_LIST] = (func[STRUCT_PAD])(func[STRUCT_LIST], maxHorseNum)
            # 標準化
            func[STRUCT_LIST] = (func[STRUCT_NRM])(func[STRUCT_LIST])
        logger.debug("padding and normalize end")

        # 各リスト確認
        logger.debug("========================================")
        # 教師データt
        logger.debug("t (len : {0})= {1}".format(len(teachList), teachList))
        # 学習データX
        logger.debug("racedbLearningList(len : {0}) = {1}".format(len(racedbLearningList), racedbLearningList))
        logger.debug("horseAgeList(len : {0}) = {1}".format(len(horseAgeList), horseAgeList))
        logger.debug("burdenWeightList(len : {0}) = {1}".format(len(burdenWeightList), burdenWeightList))
        logger.debug("postPositionList(len : {0}) = {1}".format(len(postPositionList), postPositionList))
        logger.debug("jockeyList(len : {0}) = {1}".format(len(jockeyList), jockeyList))

        # 統合
        learningList = [racedbLearningList, horseAgeList, burdenWeightList, postPositionList, jockeyList]
        
        # 一次元化
        learningList = list(deepflatten(learningList))

        # 保存用リストに追加
        totalXList.append(learningList)
        totaltList.append(teachList)

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
