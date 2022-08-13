import pickle
import os
import sys
from pathlib import Path
import logging
from datetime import date
from dateutil.relativedelta import relativedelta
import numpy as np

# commonフォルダ内読み込みのため
sys.path.append(os.path.abspath(".."))
parentDir = os.path.dirname(os.path.abspath(__file__))
if parentDir not in sys.path:
    sys.path.append(parentDir)

# 賞金リスト拡張
# 指定サイズより小さい場合に限り拡張する
# 拡張したサイズ分だけゼロをappendする
# nrmList : 拡張したいリスト
# listSize : 希望のリスト要素数
def moneyNrmExp(nrmList, listSize):
    exSize = listSize - len(nrmList)
    if exSize > 0:
        for i in range(exSize):
            nrmList.append(0)
    return nrmList

# ゴールタイムリスト拡張
# 指定サイズより小さい場合に限り拡張する
# 偏差値40の値程度でランダムに埋める
# nrmList : 拡張したいリスト
# listSize : 希望のリスト要素数
def goalTimeNrmExp(nrmList, listSize):
    exSize   = listSize - len(nrmList)
    if exSize > 0:
        nNrmList = np.array(nrmList)
        sigma    = np.std(nNrmList)
        ave      = np.average(nNrmList)
        exRandList = np.random.uniform(-2*sigma, -sigma, exSize)
        exRandList += ave
        for ex in exRandList:
            nrmList.append(ex)
    return nrmList

# 指定サイズより小さい場合に限り拡張する
# 最下位にハナ差で連続してゴールすることにする
# nrmList : 拡張したいリスト
# listSize : 希望のリスト要素数
def marginListExp(rowList, listSize):
    exSize   = listSize - len(rowList)
    lastMargin = rowList[-1]
    if exSize > 0:
        for i in range(exSize):
            lastMargin += 0.0125
            rowList.append(lastMargin)
    return rowList

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
    # 遅い時間ほど馬場が荒れていることを表現する
    t = start_time_string.split(":")
    min = float(t[0])*60 + float(t[1])
    # 最終出走時間 16:30 = 16 * 60 + 30 = 990 で割る
    min /= 990 
    return min

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
    
    # DBに一度のレースで出た馬の最大頭数を問い合わせる
    maxHorseNum = racedb.getMaxHorseNumLargestEver()

    # for race in range(len(racedb.raceID)):
    for race in range(1):
        logger.info("========================================")
        logger.info("From RaceDB info =>")
        logger.info("https://db.netkeiba.com/race/{0}".format(racedb.raceID[race]))

        # 学習リスト作成
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
        distance = float(racedb.getCourseDistance(race))
        racedbLearningList.append(distance / 3600)

        # 頭数取得
        # 最大の出馬数で割って標準化
        horseNum = float(racedb.getHorseNum(race))
        racedbLearningList.append(horseNum / maxHorseNum)

        # 賞金取得
        # ダミーデータ挿入 -> 標準化
        moneyList = racedb.getMoneyList(race)
        moneyExpList = moneyNrmExp(moneyList, maxHorseNum)
        racedbLearningList.append(racedb.moneyNrm(moneyExpList))

        # 賞金取得 その2 : 全レースの最高金額で割って正規化
        # ToDo : 最高金額を取得して割る作業を追加
        #racedbLearningList.append(racedb.getMoneyList2(race))

        ### =====ここまでが入力?
        ###      ここから下は結果(正解ラベル的な)?

        # タイム取得
        # 標準化 -> ダミーデータ挿入
        goalTimeRowList = racedb.goalTimeConv2SecList(race)
        goalTimeNrmList = racedb.goalTimeNrm(goalTimeRowList)
        goalTimeExpList = goalTimeNrmExp(goalTimeNrmList, maxHorseNum)
        racedbLearningList.append(racedb.goalTimeNrm(goalTimeExpList))

        # 着差取得
        # ダミーデータ挿入 -> 標準化
        # これを教師データtとする
        marginList = racedb.getMarginList(race)
        marginExpList = marginListExp(marginList, maxHorseNum)
        teachList = racedb.marginListNrm(marginExpList)

        logger.info("racedbLearningList = Weather, CourseCondition, RaceStartTime, CourseDistance, HorseNum, [Money], [goalTime]")
        logger.info("racedbLearningList = {0}".format(racedbLearningList))
        logger.info("teachList = {0}".format(teachList))

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
            logger.info("https://db.netkeiba.com/horse/{0} => index : {1}".format(horseID, index))
            
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
