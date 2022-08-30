# 入力X の基底クラス

import pickle
import sys
import os
import pathlib
import logging
import re
from iteration_utilities import deepflatten
from datetime import date
from dateutil.relativedelta import relativedelta
import numpy as np

from debug import *
from NetkeibaDB import *

db = NetkeibaDB()

class XClass:
    def __init__(self, maxPadSize = 24):
        print("XClass calles")
        self.xList = []
        self.padSize = maxPadSize
        self.race_id = '0'
    
    def set(self, race_id):
        self.race_id = race_id

    def get(self):
        print("this???????????")
        return self.xList

    def fix(self):
        return self.xList

    def pad(self):
        return self.xList

    def nrm(self):
        return self.xList

    def adj(self):
        if self.race_id == '0':
            print("ERROR : SET race_id")
        else:
            self.xList = self.get()
            print("get = ", self.xList)
            self.xList = self.fix()
            print("fix = ", self.xList)
            self.xList = self.pad()
            print("pad = ", self.xList)
            self.xList = self.nrm()
            print("nrm = ", self.xList)
        return self.xList

class MoneyClass(XClass):
    def __init__(self):
        super().__init__()

    def set(self, race_id):
        super().set(race_id)

    def get(self):
        print("MoneyClass get called")
        prizeList = db.getColDataFromTbl("race_result", "prize", "race_id", self.race_id)
        for i in range(len(prizeList)):
            prizeList[i] = str(prizeList[i])
        return prizeList
    
    def fix(self):
        # 賞金リストをfloat変換する
        rowList = self.xList
        moneyList = []
        for m in rowList:
            if m == "":
                fm = "0.0"
            else:
                fm = m.replace(",","")
            moneyList.append(float(fm))
        return moneyList

    def pad(self):
        # 賞金リスト拡張
        # ダミーデータ：0
        exSize = self.padSize - len(self.xList)
        if exSize > 0:
            for i in range(exSize):
                self.xList.append(0)
        return self.xList

    def nrm(self):
        # 賞金標準化
        # 1位賞金で割る
        # moneyList は float前提
        money1st = self.xList[0]
        moneyNrmList = []
        for m in self.xList:
            moneyNrmList.append(m / money1st)
        return moneyNrmList

    def adj(self):
        return XClass.adj(self)

class HorseNumClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        print("HorseNumClass get")
        self.xList = [db.getRowCnt("race_result", "race_id", self.race_id)]

    def fix(self):
        self.xList = XClass.fix(self)

    def pad(self):
        self.xList = XClass.pad(self)

    def nrm(self):
        # 最大出走馬数で割って標準化
        npcdList = np.array(self.xList)
        npcdList = npcdList / self.padSize
        self.xList = npcdList.tolist()

    def adj(self):
        print("HorseNumClass")
        self.get()
        self.fix()
        self.pad()
        self.nrm()
        return self.xList

class CourseConditionClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        raceData1List = db.getColDataFromTbl("race_result", "race_data1", "race_id", self.race_id)
        # コース状態取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = raceData1List[0].split(":")[2]
        #  良 / 発走 
        sep1 = sep1.split("/")[0]
        # 良
        sep1 = sep1.replace(" ", "")
        return sep1

    def fix(self):
        return XClass.fix(self)

    def pad(self):
        return XClass.pad()

    def nrm(self):
        # 馬場状態のone-hot表現(ただし良は全て0として表現する)
        condition_dict = {'良':-1, '稍重':0, '重':1, '不良':2}
        condition_onehot = [0] * 3
        hot_idx = condition_dict[self.xList]
        if hot_idx != -1:
            condition_onehot[hot_idx] = 1
        return condition_onehot

    def adj(self):
        return XClass.adj(self)

class CourseDistanceClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        raceData1List = db.getColDataFromTbl("race_result", "race_data1", "race_id", self.race_id)
        # 距離取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = raceData1List[0].split(":")[0]
        # 芝右1600m
        # 数字以外を削除
        sep1 = re.sub(r'\D', '', sep1)
        sep1 = sep1.replace(" ", "")
        # 他と統一するためリストにする
        return [float(sep1)]

    def fix(self):
        return XClass.fix(self)

    def pad(self):
        return XClass.pad()

    def nrm(self):
        # 最長距離で割って標準化
        MAX_DISTANCE = 3600.0
        npcdList = np.array(self.xList)
        npcdList = npcdList / MAX_DISTANCE
        return npcdList.tolist()

    def adj(self):
        return XClass.adj(self)

class RaceStartTimeClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        raceData1List = db.getColDataFromTbl("race_result", "race_data1", "race_id", self.race_id)
        # 出走時刻取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = raceData1List[0].split("/")[3]
        #  発走 : 15:35
        sep1 = sep1.split(" : ")[1]
        #  15:35
        sep1 = sep1.replace(" ", "")
        # 他と統一するためリストにする
        return [sep1]

    def fix(self):
        return XClass.fix(self)

    def pad(self):
        return XClass.pad()

    def nrm(self):
        # 発走時刻の数値化(時*60 + 分)と標準化
        # 遅い時間ほど馬場が荒れていることを表現する
        minList = []
        for i in self.xList:
            t = i.split(":")
            min = float(t[0])*60 + float(t[1])
            # 最終出走時間 16:30 = 16 * 60 + 30 = 990 で割る
            minList.append(min / 990 )
        return minList

    def adj(self):
        return XClass.adj(self)

class WeatherClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        raceData1List = db.getColDataFromTbl("race_result", "race_data1", "race_id", self.race_id)
        sep1 = raceData1List[0].split(":")[1]
        #  晴 / 芝 
        sep1 = sep1.split("/")[0]
        # 晴 
        sep1 = sep1.replace(" ", "")
        return sep1

    def fix(self):
        return XClass.fix(self)

    def pad(self):
        return XClass.pad()

    def nrm(self):
        # 天気のone-hot表現(ただし晴は全て0として表現する)
        # 出現する天気は6種類
        weather_dict = {'晴':-1, '曇':0, '小雨':1, '雨':2, '小雪':3, '雪':4}
        weather_onehot = [0] * 5
        hot_idx = weather_dict[self.xList]
        if hot_idx != -1:
            weather_onehot[hot_idx] = 1
        return weather_onehot

    def adj(self):
        return XClass.adj(self)

class HorseAgeClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        horseList = db.getColDataFromTbl("race_info", "horse_id", "race_id", self.race_id)
        bdList = []
        for horse_id in horseList:
            data = db.horse_prof_getOneData(horse_id, "bod")
            birthYear = int(data.split("年")[0])
            birthMon = int(data.split("年")[1].split("月")[0])
            birthDay = int(data.split("月")[1].split("日")[0])
            d1 = date(birthYear, birthMon, birthDay)
            bdList.append(d1)
        return bdList

    def fix(self, d0):
        # 標準化の前に誕生日を日数表記にしておく
        bdList = self.xList
        for i in range(len(bdList)):
            dy = relativedelta(d0, bdList[i])
            age = dy.years + (dy.months / 12.0) + (dy.days / 365.0)
            bdList[i] = age
        return bdList

    def pad(self):
        # 年齢リスト拡張
        # ダミーデータ：平均値
        mean_age = np.mean(self.xList)
        exSize = self.padSize - len(self.xList)
        if exSize > 0:
            for i in range(exSize):
                self.xList.append(mean_age)
        return self.xList

    def nrm(self):
        # 馬年齢標準化
        # 若いほうが強いのか, 年季があるほうが強いのか...
        # 最高値ですべてを割る
        nHorseAgeList = np.array(self.xList)
        maxAge = np.max(nHorseAgeList)
        nHorseAgeList = nHorseAgeList / maxAge
        return nHorseAgeList.tolist()

    def adj(self, d0):
        if self.race_id == '0':
            print("ERROR : SET race_id")
        else:
            self.xList = self.get()
            self.xList = HorseAgeClass.fix(self, d0)
            self.xList = self.pad()
            self.xList = self.nrm()
        return self.xList

class BurdenWeightClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        burdenWeightList = db.getColDataFromTbl("race_info", "burden_weight", "race_id", self.race_id)
        for i in range(len(burdenWeightList)):
            burdenWeightList[i] = float(burdenWeightList[i])
        return burdenWeightList

    def fix(self):
        return XClass.fix(self)

    def pad(self):
        # 斤量リスト拡張
        # ダミーデータ：平均値
        mean_weight = np.mean(self.xList)
        exSize = self.padSize - len(self.xList)
        if exSize > 0:
            for i in range(exSize):
                self.xList.append(mean_weight)
        return self.xList

    def nrm(self):
        # 斤量の標準化
        # 一律60で割る
        SCALE_PARAMETER = 60
        n_weight_list = np.array(self.xList)
        n_weight_list = n_weight_list / SCALE_PARAMETER
        return n_weight_list.tolist()

    def adj(self):
        return XClass.adj(self)

class PostPositionClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        postPositionList = db.getColDataFromTbl("race_info", "post_position", "race_id", self.race_id)
        for i in range(len(postPositionList)):
            postPositionList[i] = float(postPositionList[i])
        return postPositionList

    def fix(self):
        return XClass.fix(self)

    def pad(self):
        # 枠番リスト拡張
        # ダミーデータ：listSizeに達するまで，1から順に追加．
        exSize = self.padSize - len(self.xList)
        if exSize > 0:
            for i in range(exSize):
                self.xList.append(i%8+1)
        return self.xList

    def nrm(self):
        # 枠番標準化
        # sigmoidで標準化
        nPostPositionList = np.array(self.xList)
        nPostPositionList = 1/(1+np.exp(nPostPositionList))
        return nPostPositionList.tolist()

    def adj(self):
        return XClass.adj(self)

class JockeyClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        jockeyIDList = db.getColDataFromTbl("race_info", "jockey_id", "race_id", self.race_id)
        for i in range(len(jockeyIDList)):
            jockeyIDList[i] = str(jockeyIDList[i])
        return jockeyIDList

    def fix(self):
        # 騎手の総出場回数を求める
        jockeyIDList = self.xList
        for i in range(len(jockeyIDList)):
            cnt = db.getRowCnt("race_info", "jockey_id", jockeyIDList[i])
            jockeyIDList[i] = cnt
        return jockeyIDList

    def pad(self):
        # 騎手ダミーデータ挿入
        # ダミーデータ：出場回数50を追加．
        exSize = self.padSize - len(self.xList)
        if exSize > 0:
            for i in range(exSize):
                self.xList.append(50)
        return self.xList

    def nrm(self):
        # 騎手標準化
        # 最高値ですべてを割る
        njockeyList = np.array(self.xList)
        maxJockey = np.max(njockeyList)
        njockeyList = njockeyList / maxJockey
        return njockeyList.tolist()

    def adj(self):
        return XClass.adj(self)

class CumPerformClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        # race_id に出場した馬のリストを取得
        # 各馬の以下情報を取得、fixでパフォーマンスを計算する
        horse_list = db.getRecordDataFromTbl("race_info", "race_id", self.race_id)
        col = ["horse_id", "venue", "time", "burden_weight", "course_condition", "distance", "grade"]
        horse_info_list = []
        for horse in horse_list:
            # horse のcolレコードを取得
            race = db.getMulCol("race_info", col, "horse_id", horse)
            horse_info_list.append(race)
        return horse_info_list

    def getStandardTime(self, distance, condition, track, location):
        # レースコースの状態に依存する基準タイム(秒)を計算して返す
        # performancePredictionで予測した係数・定数を下の辞書の値に入れる．
        # loc_dictのOtherは中央競馬10か所以外の場合の値．10か所の平均値を取って作成する．
        dis_coef = 0.066433
        intercept = -9.6875
        cond_dict = {'良':-0.3145, '稍':0.1566, '重':0.1802, '不':-0.0223}
        track_dict = {'芝':-1.2514, 'ダ': 1.2514}
        loc_dict = {'札幌':1.1699, '函館':0.3113, '福島':-0.3205, '新潟':-0.2800, '東京':-0.8914,\
             '中山':0.2234, '中京':0.1815, '京都':-0.1556, '阪神':-0.4378, '小倉':0.1994, 'Other':0}

        std_time = dis_coef*distance + cond_dict[condition] + track_dict[track] + loc_dict[location] + intercept
        return std_time

    def getPerformance(self, standard_time, goal_time, weight, grade):
        # 走破タイム・斤量などを考慮し，「強さ(performance)」を計算
        # 以下のeffectの値，計算式は適当
        weight_effect = 1+ (55 - weight)/1000
        grade_effect_dict = {'G1':1.14, 'G2':1.12, 'G3':1.10, 'OP':1.0, 'J.G1':1.0, 'J.G2':1.0, 'J.G3':1.0}
        perform = (10 + standard_time - goal_time*weight_effect) * grade_effect_dict[grade]
        return perform

    def fix(self):
        # 各レースの結果から強さ(performance)を計算し，その最大値を記録していく
        # (外れ値を除くために，2番目の強さでもいいかもしれない．)
        # col = ["horse_id", "venue", "time", "burden_weight", "course_condition", "distance", "grade"]
        HORSE_ID         = 0
        VENUE            = 1
        TIME             = 2
        BURDEN_WEIGHT    = 3
        COURSE_CONDITION = 4
        DISTANCE         = 5
        GRADE            = 6
        loc_list = ['札幌', '函館', '福島', '新潟', '東京', '中山', '中京', '京都', '阪神', '小倉']
        max_performance_list = []
        performance = 0

        # raw = [[(馬Aレースa情報), (馬Aレースb情報), ... ], [(馬Bレースc情報), (馬Bレースd情報), ...]]
        for race in self.xList:
            for horse_info in race:
                # horse_info = ('1982106916', '3小倉8', '1:12.7', '53', '良', '芝1200', '-1')
                max_performance = -1000.0
                # ゴールタイムを取得
                goaltime = horse_info[TIME]
                try:
                    goaltime_sec = float(goaltime.split(':')[0])*60 + float(goaltime.split(':')[1])
                except:
                    goaltime_sec = 240
                # 斤量を取得
                try:
                    burden_weight = float(horse_info[BURDEN_WEIGHT])
                except:
                    burden_weight = 40
                # 馬場状態を取得
                condition = horse_info[COURSE_CONDITION]
                # 競馬場を取得
                location = horse_info[VENUE]
                if location not in loc_list:
                    location = "Other"
                # 芝かダートか
                if horse_info[DISTANCE][0] == "芝":
                    track = "芝"
                elif horse_info[DISTANCE][0] == "ダ":
                    track = "ダ"
                else:
                    track = "E"
                # コースの距離
                dis_str = horse_info[DISTANCE]
                try:
                    distance = float(re.sub(r'\D', '', dis_str).replace(" ", ""))
                except:
                    distance = "E"
                # レースのグレード (G1,G2,G3,OP)
                # 日本の中央競馬以外のレースは全てOP扱いになる
                grade = horse_info[GRADE]
                if grade == "-1":
                    grade = "OP"
                else:
                    grade = "G" + grade

                # 計算不能な場合を除いてperformanceを計算
                if track != "E" and distance != "E":
                    standard_time = self.getStandardTime(distance, condition, track, location)
                    performance = self.getPerformance(standard_time, goaltime_sec, burden_weight, grade)

                if performance > max_performance:
                    max_performance = performance

            max_performance_list.append(max_performance)

        return max_performance_list

    def pad(self):
        exSize = self.padSize - len(self.xList)
        if exSize > 0:
            for i in range(exSize):
                self.xList.append(0)
        return self.xList

    def nrm(self):
        return XClass.nrm()

    def adj(self):
        return XClass.adj(self)

class MarginClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        marginList = db.getColDataFromTbl("race_result", "margin", "race_id", self.race_id)
        for i in range(len(marginList)):
            marginList[i] = str(marginList[i])
        return marginList

    def fix(self):
        # 着差をfloatにして返す
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
        for i in range(len(self.xList)):
            margin = self.xList[i]
            # 'クビ+1/2' などの特殊な表記に対応する
            if '+' in margin:
                m = margin.split('+')
                time += marginDict[m[0]]
                time += marginDict[m[1]]
            else:
                time += marginDict[margin]
            retList.append(time)
        return retList

    def pad(self):
        # 着差リスト拡張
        # ダミーデータ：最下位にハナ差で連続してゴールすることにする
        HANA = 0.0125
        exSize   = self.padSize - len(self.xList)
        lastMargin = self.xList[-1]
        if exSize > 0:
            for i in range(exSize):
                lastMargin += HANA
                self.xList.append(lastMargin)
        return self.xList

    def nrm(self):
        # 着差標準化
        x = np.array(self.xList)
        ny = 1/(1+np.exp(-x))
        y = ny.tolist()
        # リストを逆順にする。元のリストを破壊するため注意。
        # 戻り値はNoneであることも注意
        y.reverse()
        return y

    def adj(self):
        return XClass.adj(self)

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

class MgrClass(
    HorseNumClass, CourseConditionClass, CourseDistanceClass, RaceStartTimeClass, WeatherClass,
    HorseAgeClass, BurdenWeightClass, PostPositionClass, JockeyClass, CumPerformClass
    ):
    def __init__(self):
        super().__init__()
        self.x = []

    def set(self, race_id):
        super().set(race_id)

    def adj(self, race_date):
        for func in XTbl:
            print(func)
            instance = func()
            if func == HorseAgeClass:
                self.x.append(instance.adj(race_date))
            else:
                self.x.append(instance.adj())

    def get(self):
        return list(deepflatten(self.x))

class TMgrClass():
    def __init__(self):
        self.margin = MarginClass()
        self.funcList = [
            self.margin
        ]

    def set(self, race_id):
        for func in self.funcList:
            func.set(race_id)

    def adj(self):
        for func in self.funcList:
            func.adj()

    def get(self):
        x = []
        for func in self.funcList:
            x.append(func.xList)
        return list(deepflatten(x))


if __name__ == "__main__":
    x = MgrClass()
    race_id = "198606050810"
    x.set(race_id)
    x.adj(date(2022,1,1))
    print(x.get())
