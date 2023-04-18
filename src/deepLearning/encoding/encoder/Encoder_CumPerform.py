import logging
import re
import numpy as np

from Encoder_X import XClass
from debug     import stream_hdl, file_hdl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("CumPerformClass"))

class CumPerformClass(XClass):

    def __init__(self):
        super().__init__()

        # 辞書定義
        self.cond_dict = {'良':-0.3145, '稍':0.1566, '重':0.1802, '不':-0.0223}
        self.track_dict = {'芝':-1.2514, 'ダ': 1.2514}
        self.loc_dict = {'札幌':1.1699, '函館':0.3113, '福島':-0.3205, '新潟':-0.2800, '東京':-0.8914,\
                        '中山':0.2234, '中京':0.1815, '京都':-0.1556, '阪神':-0.4378, '小倉':0.1994, 'Other':0}

    def getForCalcPerformInfo(self, horse_list):
        horse_info_list = []
        for horse in horse_list:
            race = self.nf.db_horse_list_perform(horse)
            horse_info_list.append(race)
        self.xList = horse_info_list

    def get(self):
        # race_id に出場した馬のリストを取得
        # fixでパフォーマンスを計算する
        horse_list = self.nf.db_race_list_horse_id(self.race_id)
        self.getForCalcPerformInfo(horse_list)

    def getStandardTime(self, distance, condition, track, location):
        # レースコースの状態に依存する基準タイム(秒)を計算して返す
        # performancePredictionで予測した係数・定数を下の辞書の値に入れる．
        # loc_dictのOtherは中央競馬10か所以外の場合の値．10か所の平均値を取って作成する．
        dis_coef = 0.066433
        intercept = -9.6875
        
        std_time = dis_coef*distance + self.cond_dict[condition] + self.track_dict[track] + self.loc_dict[location] + intercept
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
                # logger.debug("horse_info = {0}".format(horse_info))
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
                # condition が辞書にないなら良にしておく
                if not(condition in self.cond_dict.keys()):
                    condition = '良'
                # 競馬場を取得 '3小倉8' のような数字が入っていることがあるので数字を削除
                location = re.sub(r'[0-9]+', '', horse_info[VENUE])
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
                    # TODO: race_id = 201306050111 のような距離の近くに別な数字があるときも問題ないか確認
                    distance = float(re.sub(r'\D', '', dis_str).replace(" ", ""))
                except:
                    distance = "E"
                # レースのグレード (G1,G2,G3,OP)
                # 日本の中央競馬以外のレースは全てOP扱いになる
                grade = horse_info[GRADE]
                if grade == "1" or grade =="2" or grade=="3":
                    grade = "G" + grade
                else:
                    grade = "OP"

                # 計算不能な場合を除いてperformanceを計算
                if track != "E" and distance != "E":
                    standard_time = self.getStandardTime(distance, condition, track, location)
                    performance = self.getPerformance(standard_time, goaltime_sec, burden_weight, grade)

                if performance > max_performance:
                    max_performance = performance

            max_performance_list.append(max_performance)

        self.xList = max_performance_list

    def nrm(self):
        # sigmoidで標準化
        # nPerformList = np.array(self.xList)
        # nPerformList = 1/(1+np.exp(nPerformList))
        # self.xList = nPerformList.tolist()
        
        nPerformList = self.zscore(self.xList, axis=-1, reverse=False)
        self.xList = nPerformList.tolist()
