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

    # レース情報読み込み
    with open("../../dst/scrapingResult/racedb.pickle", 'rb') as f:
            racedb = pickle.load(f)

    # 馬情報読み込み
    with open("../../dst/scrapingResult/horsedb.pickle", 'rb') as f:
            horsedb = pickle.load(f)
    
    # サンプルで出力するレースのインデックス
    printIdx = 0

    # レースの情報一覧出力
    racedb.printAllMethodIndex(printIdx)

    # レースでのタイムをsecに変換する
    racedb.goalTimeConv2Sec(printIdx)

    # レースタイムを正規化
    racedb.goalTimeNrm(printIdx)

    # レース開催日
    d0 = racedb.getRaceDate(printIdx)

    # 出走馬の情報一覧出力
    horseOldList = []
    jockeyIDList = []
    for horseID in racedb.horseIDs_race[printIdx]:
        index = horsedb.getHorseInfo(horseID)
        horsedb.printAllMethodIndex(index)

        # 騎手出力
        jokeyID = horsedb.getJockeyID(index, racedb.raceID[printIdx])
        jockeyIDList.append(jokeyID)

        # レース開催日の馬の年齢を計算
        d1 = horsedb.getBirthDay(index)
        dy = relativedelta(d0, d1)

        # 月, 日 も小数点以下で表現した歳にする
        # 小数点以下閏年未考慮
        horseOldList.append(dy.years + (dy.months / 12.0) + (dy.days / 365.0))

    # 1位賞金出力
    racedb.moneyNrm(printIdx)
    logger.debug(racedb.money[printIdx])

    # 出場騎手参戦回数出力
    logger.debug(jockeyIDList)
    for jockey in jockeyIDList:
        cnt = horsedb.countJockeyAppear(jockey)
        logger.debug("Jockey ID {0} : count = {1}".format(jockey, cnt))
