from http.client import MULTI_STATUS
from datetime import date
import numpy as np
import os
import sys
import logging
import re

# スクレイピング側とAI側で扱うパラメータを共通化するためのインタフェースとして機能する
# スクレイピングで取得するパラメータを変更する場合、ここをメンテすること
# pickleで保存できなくなるのでファイル読み書き系処理は追加しないこと

# debug initialize
# LEVEL : DEBUG < INFO < WARNING < ERROR < CRITICAL
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#logging.disable(logging.DEBUG)

# ENUM race_data
# race_data = [raceID, race_name, race_data1, race_data2, horseIDs_race, goal_time, goal_dif, horse_weight, money]
# '198601010809'
# '第22回札幌記念(G3)'
# 'ダ右2000m / 天候 : 曇 / ダート : 良 / 発走 : 15:50'
# '1986年6月29日 1回札幌8日目 4歳以上オープン  (混)(ハンデ)'
# ['1982101018', '1981101906', '1981105792', '1980103815', '1981101953', '1982102717', '1981100539', '1980103942']
# ['2:02.3', '2:03.1', '2:03.4', '2:03.7', '2:03.9', '2:04.7', '2:04.9', '2:06.3']
# ['', '5', '2', '2', '1.1/4', '5', '1', '9']
# ['506(+12)', '516(+2)', '548(0)', '496(+8)', '488(-6)', '462(-4)', '502(-2)', '530(0)']
# ['2,700.0', '1,100.0', '680.0', '410.0', '270.0', '', '', '']

class RaceDB:
    def __init__(self):
        self.raceID = []
        self.race_name = []
        self.race_data1 = []
        self.race_data2 = []
        self.horseIDs_race = []
        self.goal_time = []
        self.goal_dif = []
        self.horse_weight = []
        self.money = []

    # 一貫性チェック
    # すべての要素の数は同じである必要がある
    def selfConsistencyCheck(self):
        lengthMtr = len(self.raceID)
        errMsg  = "CHECK RaceDB CONSISTENCY !! => (len(raceID) != len({0})) == ({1} != {2})"
        consisFlg = True

        lengthSlv = len(self.race_name)
        if lengthMtr != lengthSlv:
            logger.critical(errMsg.format("race_name", lengthMtr, lengthSlv))
            consisFlg = False

        lengthSlv = len(self.race_data1)
        if lengthMtr != lengthSlv:
            logger.critical(errMsg.format("race_data1", lengthMtr, lengthSlv))
            consisFlg = False

        lengthSlv = len(self.race_data2)
        if lengthMtr != lengthSlv:
            logger.critical(errMsg.format("race_data2", lengthMtr, lengthSlv))
            consisFlg = False

        lengthSlv = len(self.goal_time)
        if lengthMtr != lengthSlv:
            logger.critical(errMsg.format("goal_time", lengthMtr, lengthSlv))
            consisFlg = False

        lengthSlv = len(self.goal_dif)
        if lengthMtr != lengthSlv:
            logger.critical(errMsg.format("goal_dif", lengthMtr, lengthSlv))
            consisFlg = False

        lengthSlv = len(self.horse_weight)
        if lengthMtr != lengthSlv:
            logger.critical(errMsg.format("horse_weight", lengthMtr, lengthSlv))
            consisFlg = False

        lengthSlv = len(self.money)
        if lengthMtr != lengthSlv:
            logger.critical(errMsg.format("money", lengthMtr, lengthSlv))
            consisFlg = False

        logger.info("Self consistency check : PASS (length = {})".format(lengthMtr))
        return consisFlg
    
    def printAllMethodIndex(self, index):
        logger.info("raceID => ")
        logger.info(self.raceID[index])
        logger.info("race_name => ")
        logger.info(self.race_name[index])
        logger.info("race_data1 => ")
        logger.info(self.race_data1[index])
        logger.info("race_data2 => ")
        logger.info(self.race_data2[index])
        logger.info("horseIDs_race => ")
        logger.info(self.horseIDs_race[index])
        logger.info("goal_time => ")
        logger.info(self.goal_time[index])
        logger.info("goal_dif => ")
        logger.info(self.goal_dif[index])
        logger.info("horse_weight => ")
        logger.info(self.horse_weight[index])
        logger.info("money => ")
        logger.info(self.money[index])

    # 各パラメータセッタ
    def appendRaceID(self, data):
        self.raceID.append(data)

    def appendRaceName(self, data):
        self.race_name.append(data)

    def appendRaceData1(self, data):
        self.race_data1.append(data)

    def appendRaceData2(self, data):
        self.race_data2.append(data)

    def appendHorseIDsRace(self, data):
        self.horseIDs_race.append(data)

    def appendGoalTime(self, data):
        self.goal_time.append(data)

    def appendGoalDiff(self, data):
        self.goal_dif.append(data)

    def appendHorseWeight(self, data):
        self.horse_weight.append(data)

    def appendMoney(self, data):
        self.money.append(data)

    # horseIDs_raceを1次元配列に直して出力
    def getHorseIDList(self):
        output = []
        for i in range(len(self.horseIDs_race)):
            output += self.horseIDs_race[i]
        return output

    def goalTimeConv2Sec(self, row):
        # 秒に変換したタイムを返す
        # row = '2:02.3'
        min = float(row.split(':')[0])
        sec = float(row.split(':')[1])
        sec = min * 60 + sec
        return sec

    def getGoalTime(self, horseid, raceidx):
        sec = 130.0
        for i in range(len(self.horseIDs_race[raceidx])):
            if self.horseIDs_race[raceidx][i] == horseid:
                sec = self.goalTimeConv2Sec(self.goal_time[raceidx][i])
                break
        return sec

    def goalTimeConv2SecList(self, index):
        # ex: ['2:02.3', '2:03.1', '2:03.4', '2:03.7', '2:03.9', '2:04.7', '2:04.9', '2:06.3']
        # ->  [122.3   , 123.1   , 123.4   , 123.7   , 123.9   , 124.7   , 124.9   , 126.3]
        timeList = []
        for gtime in self.goal_time[index]:
            sec = self.goalTimeConv2Sec(gtime)
            timeList.append(sec)
        return timeList

    def getRaceDate(self, index):
        # レース開催日を取り出す
        # 以下の前提で計算する
        # race_data2 にレース開催日が含まれていること
        raceDate = self.race_data2[index]
        raceDateYear = int(raceDate.split("年")[0])
        raceDateMon = int(raceDate.split("年")[1].split("月")[0])
        raceDateDay = int(raceDate.split("月")[1].split("日")[0])
        return date(raceDateYear, raceDateMon, raceDateDay)

    def getMoneyList(self, index):
        # 賞金リストを返す
        moneyList = []
        for m in self.money[index]:
            if m == "":
                fm = "0.0"
            else:
                fm = m.replace(",","")
            moneyList.append(float(fm))
        return moneyList

    def getMoneyList2(self, index):
        # 賞金リストを持ってくる．
        # 空の要素はゼロyenにする
        money_list = [0] * len(self.money[index])
        for m in range(len(self.money[index])):
            if self.money[index][m] == "":
                fm = "0.0"
            else:
                fm = self.money[index][m].replace(",","")
            self.money[index][m] = float(fm)
        
        return money_list

    def getWeather(self, index):
        # 天気取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = self.race_data1[index].split(":")[1]
        #  晴 / 芝 
        sep1 = sep1.split("/")[0]
        # 晴 
        sep1 = sep1.replace(" ", "")

        return sep1

    def getCourseCondition(self, index):
        # コース状態取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = self.race_data1[index].split(":")[2]
        #  良 / 発走 
        sep1 = sep1.split("/")[0]
        # 良
        sep1 = sep1.replace(" ", "")

        return sep1

    def getRaceStartTime(self, index):
        # 出走時刻取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = self.race_data1[index].split("/")[3]
        #  発走 : 15:35
        sep1 = sep1.split(" : ")[1]
        #  15:35
        sep1 = sep1.replace(" ", "")

        return sep1
    
    def getCourseDistance(self, index):
        # 距離取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = self.race_data1[index].split(":")[0]
        # 芝右1600m
        # 数字以外を削除
        sep1 = re.sub(r'\D', '', sep1)
        sep1 = sep1.replace(" ", "")

        return float(sep1)

    def getHorseNum(self, index):
        # 頭数取得
        return len(self.horseIDs_race[index])

    def getHorseWeight(self, index):
        # 馬の体重
        # 増減は考慮しない
        # ['454(+2)', '462(+4)', '470(0)', '434(-8)', '438(+4)', '472(-6)']
        fweight = []
        for weight in self.horse_weight[index]:
            weight = weight.split("(")[0]
            fweight.append(float(weight))
        return fweight

    def getMarginList(self, raceidx):
        # 着差を返す
        # 着差の種類は以下の通り。これ以外は存在しない。
        # 同着 - 写真によっても肉眼では差が確認できないもの - タイム差は0 = 0
        # ハナ差（鼻差） - スリットの数は3 - タイム差は0 = 0.0125
        # アタマ差（頭差） - スリットの数は6 - タイム差は0 = 0.025
        # クビ差（首差、頸差） - スリットの数は12 - タイム差は0〜1/10秒 = 0.05
        # 1/2馬身（半馬身） - スリットの数は24 - タイム差は1/10秒 = 0.1
        # 3/4馬身 - スリットの数は30 - タイム差は1/10〜2/10秒 = 0.15
        # 1馬身 - スリットの数は33 - タイム差は2/10秒 = 0.2
        # 1 1/4馬身（1馬身と1/4） - スリットの数は37 - タイム差は2/10秒 = 0.2
        # 1 1/2馬身（1馬身と1/2） - タイム差は2/10〜3/10秒 = 0.25
        # 1 3/4馬身（1馬身と3/4） - タイム差は3/10秒 = 0.3
        # 2馬身 - タイム差は3/10秒 = 0.3
        # 2 1/2馬身 - タイム差は4/10秒 =  0.4
        # 3馬身 - タイム差は5/10秒 = 0.5
        # 3 1/2馬身 - タイム差は6/10秒 = 0.6
        # 4馬身 - タイム差は7/10秒 = 0.7
        # 5馬身 - タイム差は8/10〜9/10秒 = 0.9
        # 6馬身 - タイム差は1秒 = 1.0
        # 7馬身 - タイム差は11/10〜12/10秒 = 1.2
        # 8馬身 - タイム差は13/10秒 = 1.3
        # 9馬身 - タイム差は14/10〜15/10秒 = 1.5
        # 10馬身 - タイム差は16/10秒   = 1.6
        # 大差 - タイム差は17/10秒以上 = 1.7
        # ['', '5', '2', '2', '1.1/4', '5', '1', '9']
        marginDict = {'同着':0, '':0, 'ハナ':0.0125, 'アタマ':0.025, 'クビ':0.05, '1/2':0.1, '3/4':0.15, '1':0.2, \
                      '1.1/4':0.2, '1.1/2':0.25, '1.3/4':0.3, '2':0.3, '2.1/2':0.4, '3':0.5, '3.1/2':0.6, '4':0.7, '5':0.9, \
                      '6':1.0, '7':1.2, '8':1.3, '9':1.5, '10':1.6, '大':1.7}
        time = 0
        retList = []
        for i in range(len(self.horseIDs_race[raceidx])):
            margin = self.goal_dif[raceidx][i]
            time += marginDict[margin]
            retList.append(time)
        return retList

    def getMaxHorseNumLargestEver(self):
        # 1つのレースに出場した最大の頭数を調べる
        max =  0
        for i in self.horseIDs_race:
            horseNum = len(i)
            if max < horseNum:
                max = horseNum
        return max
