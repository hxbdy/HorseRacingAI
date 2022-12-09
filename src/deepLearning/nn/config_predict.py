# 学習済みパラメータからレース結果を予測する
# 学習済みパラメータを dst\trainedParam\newest から読み込む
# 入力データ(予測したいレース情報)を手入力してください
# 入力されたレース情報から実際に推論を実行し、結果を出力するのは src\deepLearning\nn\predict.py

from datetime import date
from getFromDB import db_horse_bod, db_horse_father

import encoder

# 推測したいレース情報入力
# ジャパンカップ
# https://race.netkeiba.com/race/shutuba.html?race_id=202205050812&rf=top_pickup
# 結果
# 
# ==========================================================================

# レース当日入力フィールド
# horse_id
horse_id_list = ['2019190003', '2019190002', '2017105567', '2015100831', '2016190001', '2017105082', '2019190004', '2017100720', '2016110103', '2016104887', '2016106606', '2016104791', '2018106545', '2019105195', '2018105165', '2013103569', '2018102167', '2016104618']
# 賞金リスト
money_list = ["40000","16000","10000","6000","4000"]
# 出走する馬の頭数
horse_num = [18]
# コース状態
# '良', '稍重', '重', '不良' のいずれか
course_condition = '良'
# コース長
course_distance = [2400.0]
# 出走時刻
start_time = "15:40"
# 天気
# '晴', '曇', '小雨', '雨', '小雪', '雪' のいずれか
weather = '晴'
# レース開催日
race_date = date(2022, 11, 27)
# 斤量
burden_weight = [55.0, 55.0, 57.0, 57.0, 55.0, 57.0, 55.0, 55.0, 57.0, 57.0, 57.0, 55.0, 57.0, 55.0, 57.0, 57.0, 55.0, 57.0]
# 枠番
post_position = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 7, 8, 8, 8]
# 騎手ID
jockey_id_list =  ['05498', '05339', '05585', '01117', '05464', '05366', 'a04a7', '05626', '01125', '00666', '01179', '01126', '01144', '01088', '05473', '01150', '05212', '01115']
# レースID
today_race_id = "202205050812"


# ==========================================================================
# レース当日は以下メンテ不要
class PredictMoneyClass(encoder.Encoder_Money.MoneyClass):
    def get(self):
        # 賞金リスト
        self.xList = money_list
class PredictHorseNumClass(encoder.Encoder_HorseNum.HorseNumClass):
    def get(self):
        # 出走する馬の頭数
        self.xList = horse_num
class PredictCourseConditionClass(encoder.Encoder_CourseCondition.CourseConditionClass):
    def get(self):
        # コース状態
        # '良', '稍重', '重', '不良' のいずれか
        self.xList = course_condition
class PredictCourseDistanceClass(encoder.Encoder_CourseDistance.CourseDistanceClass):
    def get(self):
        # コース長
        self.xList = course_distance
class PredictRaceStartTimeClass(encoder.Encoder_RaceStartTime.RaceStartTimeClass):
    def get(self):
        # 出走時刻
        self.xList = start_time
class PredictWeatherClass(encoder.Encoder_Weather.WeatherClass):
    def get(self):
        # 天気
        # '晴', '曇', '小雨', '雨', '小雪', '雪' のいずれか
        self.xList = weather
class PredictHorseAgeClass(encoder.Encoder_HorseAge.HorseAgeClass):
    def get(self):
        # レース開催日
        self.d0 = race_date

        # 誕生日をDBから取得
        bdList = []
        for horse_id in horse_id_list:
            bod = db_horse_bod(horse_id)
            bdList.append(bod)
        self.xList = bdList        
class PredictBurdenWeightClass(encoder.Encoder_BurdenWeight.BurdenWeightClass):
    def get(self):
        # 斤量
        self.xList = burden_weight
class PredictPostPositionClass(encoder.Encoder_PostPosition.PostPositionClass):
    def get(self):
        # 枠番
        self.xList = post_position
class PredictJockeyClass(encoder.Encoder_Jockey.JockeyClass):
    def get(self):
        # jockey_id
        self.xList = jockey_id_list
        # race_id
        self.race_id = today_race_id
class PredictCumPerformClass(encoder.Encoder_CumPerform.CumPerformClass):
    def get(self):
        # horse_id
        self.getForCalcPerformInfo(horse_id_list)
class PredictBradleyTerryClass(encoder.Encoder_BradleyTerry.BradleyTerryClass):
    def get(self):
        # horse_id
        self.xList = horse_id_list
        self.col_num = len(self.xList)
class PredictUmamusumeClass(encoder.Encoder_Umamusume.UmamusumeClass):
    def get(self):
        # horse_id
        self.xList = horse_id_list
class PredictParentBradleyTerryClass(encoder.Encoder_ParentBradleyTerry.ParentBradleyTerryClass):
    def get(self):
        # horse_id
        childList = horse_id_list
        parentList = []
        for i in range(len(childList)):
            # 父のidを取得
            parent = db_horse_father(childList[i])
            parentList.append(parent)
        self.xList = parentList
        self.col_num = len(self.xList)
class PredictLast3fClass(encoder.Encoder_Last3f.Last3fClass):
    def get(self):
        # race_id
        self.race_id = today_race_id
        # horse_id
        self.xList = horse_id_list
