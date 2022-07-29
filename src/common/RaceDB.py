import numpy as np
import os
import sys

# スクレイピング側とAI側で扱うパラメータを共通化するためのインタフェースとして機能する
# スクレイピングで取得するパラメータを変更する場合、ここをメンテすること
# pickleで保存できなくなるのでファイル読み書き系処理は追加しないこと

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
        
    def goalTimeNrm(self,index):
        # sigmoid で標準化
        # 計算式 : y = 1 / (1 + exp(x))
        # テキストではexp(-x)だが今回は値が小さい方が「良いタイム」のためexp(x)としてみた
        # 例えば90[sec]をそのまま入れると exp(90)を計算することになり
        # y = 0 に近づきすぎるため良くないと思うので一度最大値で割っておく
        # 最大値 = 最下位のタイム
        npGoalTime = np.array(self.goal_time[index])
        c = np.max(npGoalTime)
        y = 1 / (1 + np.exp(npGoalTime / c))
        # ndarray と list の違いがよくわかっていないので一応リストに変換しておく
        self.goal_time[index] = y.tolist()

    def goalTimeConv2Sec(self, index):
        # ex: ['2:02.3', '2:03.1', '2:03.4', '2:03.7', '2:03.9', '2:04.7', '2:04.9', '2:06.3']
        # ->  [122.3   , 123.1   , 123.4   , 123.7   , 123.9   , 124.7   , 124.9   , 126.3]
        for gtime in range(len(self.goal_time[index])):
            min = float(self.goal_time[index][gtime].split(':')[0])
            sec = float(self.goal_time[index][gtime].split(':')[1])
            # 秒に変換したタイムをリストに入れ直す
            self.goal_time[index][gtime] = min * 60 + sec
