import os
import sys

# スクレイピング側とAI側で扱うパラメータを共通化するためのインタフェースとして機能する
# スクレイピングで取得するパラメータを変更する場合、ここをメンテすること
# pickleで保存できなくなるのでファイル読み書き系処理は追加しないこと

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

    # 各パラメータゲッタ
    def getRaceID(self, data):
        return self.raceID

    def getRaceName(self, data):
        return self.race_name

    def getRaceData1(self):
        return self.race_data1

    def getRaceData2(self):
        return self.race_data2

    def getHorseIDsRace(self):
        return self.horseIDs_race

    def getGoalTime(self):
        return self.goal_time

    def getGoalDiff(self):
        return self.goal_dif

    def getHorseWeight(self):
        return self.horse_weight

    def getMoney(self):
        return self.money
