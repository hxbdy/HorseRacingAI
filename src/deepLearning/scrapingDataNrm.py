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
    with open("../../dst/scrapingResult/raceGradedb.pickle", 'rb') as f:
            gradedb = pickle.load(f)
    
    logger.info("Database loading complete")

    # for race in range(len(racedb.raceID)):
    for race in range(1):
        logger.info("========================================")
        logger.info("From RaceDB info =>")
        logger.info("RaceID : {0}".format(racedb.raceID[race]))

        # 学習リスト作成
        racedbLearningList = []

        # 天気取得
        # ToDo : 数値化, 標準化
        racedbLearningList.append(racedb.getWeather(race))

        # コース状態取得
        # ToDo : 数値化, 標準化
        racedbLearningList.append(racedb.getCourseCondition(race))

        # 出走時刻取得
        # ToDo : 数値化, 標準化
        racedbLearningList.append(racedb.getRaceStartTime(race))

        # 距離取得
        # ToDo : 標準化
        racedbLearningList.append(racedb.getCourseDistance(race))

        # 頭数取得
        # ToDo : 標準化
        racedbLearningList.append(racedb.getHorseNum(race))

        # タイム取得
        # ToDo : 標準化
        racedbLearningList.append(racedb.goalTimeConv2SecList(race))

        # 着差取得
        # ToDo : 標準化
        racedbLearningList.append(racedb.getMarginList(race))

        # 賞金取得
        # ToDo : 標準化
        racedbLearningList.append(racedb.getMoneyList(race))

        logger.info("racedbLearningList = Weather, CourseCondition, RaceStartTime, CourseDistance, HorseNum, [goalTime], [Margin], [Money]")
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
