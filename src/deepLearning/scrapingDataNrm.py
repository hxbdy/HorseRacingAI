import pickle
import os
import sys
from pathlib import Path
import logging
from datetime import date
from dateutil.relativedelta import relativedelta

# commonフォルダ内読み込みのため
sys.path.append(os.path.abspath(".."))
parentDir = os.path.dirname(os.path.abspath(__file__))
if parentDir not in sys.path:
    sys.path.append(parentDir)

def nrmWeather(weather_string):
    # 天気のone-hot表現(ただし晴は全て0として表現する)
    # 出現する天気は6種類
    weather_dict = {'晴':-1, '曇':0, '小雨':1, '雨':2, '小雪':3, '雪':4}
    weather_onehot = [0] * 5
    hot_idx = weather_dict[weather_string]
    if hot_idx != -1:
        weather_onehot[hot_idx] = 1
    
    return weather_onehot

def nrmCourseCondition(condition_string):
    # 馬場状態のone-hot表現(ただし良は全て0として表現する)
    condition_dict = {'良':-1, '稍重':0, '重':1, '不良':2}
    condition_onehot = [0] * 3
    hot_idx = condition_dict[condition_string]
    if hot_idx != -1:
        condition_onehot[hot_idx] = 1

    return condition_onehot

def nrmRaceStartTime(start_time_string):
    # 発送時刻の数値化 時*60 + 分
    t = start_time_string.split(":")

    return int(t[0])*60 + int(t[1])

if __name__ == "__main__":
    # debug initialize
    # LEVEL : DEBUG < INFO < WARNING < ERROR < CRITICAL
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s [%(levelname)s] %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    #logging.disable(logging.DEBUG)

    # pickle読み込み
    logger.info("Database loading start ...")

    # レース情報読み込み
    with open("../../dst/scrapingResult/racedb.pickle", 'rb') as f:
            racedb = pickle.load(f)

    # 馬情報読み込み
    with open("../../dst/scrapingResult/horsedb.pickle", 'rb') as f:
            horsedb = pickle.load(f)

    # G1-3情報読み込み
    # with open("../../dst/scrapingResult/raceGradedb.pickle", 'rb') as f:
        #gradedb = pickle.load(f)
    
    logger.info("Database loading complete")

    # for race in range(len(racedb.raceID)):
    for race in range(1):
        logger.info("========================================")
        logger.info("From RaceDB info =>")
        logger.info("RaceID : {0}".format(racedb.raceID[race]))

        # 学習リスト作成
        racedbLearningList = []

        # 天気取得
        # ToDo : 数値化, 標準化 -> onehot表現 5列使用
        # (わりとどうでもよい変数だと思うので，1変数に圧縮してもよいと思う)
        for i in nrmWeather(racedb.getWeather(race)):
            racedbLearningList.append(i)

        # コース状態取得
        # ToDo : 数値化, 標準化 -> onehot表現 3列使用
        # (1変数にしやすい変数であるが，onehotにして重みは学習に任せた方が良いと思う)
        for i in nrmCourseCondition(racedb.getCourseCondition(race)):
            racedbLearningList.append(i)

        # 出走時刻取得
        # ToDo : 数値化, 標準化 -> 数値化
        # (遅い時間ほど馬場が荒れていることを表現?)
        racedbLearningList.append(nrmRaceStartTime(racedb.getRaceStartTime(race)))

        # 距離取得
        # ToDo : 標準化 -> racedb内で数値化済
        racedbLearningList.append(racedb.getCourseDistance(race))

        # 頭数取得
        # ToDo : 標準化 -> racedb内で数値化済
        racedbLearningList.append(racedb.getHorseNum(race))

        # 賞金取得
        # ToDo : 標準化
        racedbLearningList.append(racedb.getMoneyList(race))

        # 賞金取得 その2 : 全レースの最高金額で割って正規化
        # ToDo : 最高金額を取得して割る作業を追加
        #racedbLearningList.append(racedb.getMoneyList2(race))

        ### =====ここまでが入力?
        ###      ここから下は結果(正解ラベル的な)?

        # タイム取得
        goalTimeRowList = racedb.goalTimeConv2SecList(race)
        racedbLearningList.append(racedb.goalTimeNrm(goalTimeRowList))

        # 着差取得
        marginList = racedb.getMarginList(race)
        racedbLearningList.append(racedb.marginListNrm(marginList))

        logger.info("racedbLearningList = Weather, CourseCondition, RaceStartTime, CourseDistance, HorseNum, [Money], [goalTime], [Margin]")
        logger.info("racedbLearningList = {0}".format(racedbLearningList))

        # レース開催日取得
        d0 = racedb.getRaceDate(race)

        # === horsedb問い合わせ ===
        for horseID in racedb.horseIDs_race[race]:
            logger.info("========================================")
            logger.info("From HorseDB info =>")
            
            # 学習リスト作成
            horsedbLearningList = []
            
            # horsedb へ horseID の情報は何番目に格納しているかを問い合わせる
            # 以降horsedbへの問い合わせは index を使う
            index = horsedb.getHorseInfo(horseID)
            logger.info("horseID : {0} => index : {1}".format(horseID, index))
            
            # 生涯獲得金取得
            # race時点での獲得賞金を取得
            # horsedb.getTotalEarned(index)

            # 通算成績取得[1st,2nd,3rd]
            # race開催時点での獲得賞金を取得
            # horsedb.getTotalWLRatio(index)

            # 出走当時の年齢取得(d0 > d1)
            # ToDo : 標準化
            d1 = horsedb.getBirthDay(index)
            age = horsedb.ageNrm(d0, d1)
            horsedbLearningList.append(age)

            # 着順取得
            # すでに着順ソートされているため不要

            # 斤量取得
            # ToDo : 標準化
            burdenWeight = horsedb.getBurdenWeight(index, racedb.raceID[race])
            horsedbLearningList.append(burdenWeight)

            # 枠番取得
            # ToDo : 標準化
            postPosition = horsedb.getPostPosition(index, racedb.raceID[race])
            horsedbLearningList.append(postPosition)

            # 騎手取得
            # ToDo : 標準化
            jockeyID = horsedb.getJockeyID(index, racedb.raceID[race])
            horsedbLearningList.append(jockeyID)

            logger.info("horsedbLearningList = [HorseAge, BurdenWeight, PostPosition, JockeyID]")
            logger.info("horsedbLearningList = {0}".format(horsedbLearningList))
