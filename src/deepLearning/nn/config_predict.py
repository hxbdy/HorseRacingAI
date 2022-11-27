# 学習済みパラメータからレース結果を予測する
# 学習済みパラメータを dst\trainedParam\newest から読み込む
# 入力データ(予測したいレース情報)を手入力してください
# 入力されたレース情報から実際に推論を実行し、結果を出力するのは src\deepLearning\nn\predict.py

from datetime import date
from getFromDB import db_horse_bod

import encoder

# 推測したいレース情報入力
# ジャパンカップ
# https://race.netkeiba.com/race/shutuba.html?race_id=202205050812&rf=top_pickup
# 結果
# 
# ==========================================================================

# horse_id
horse_id_list = ['2019190003', '2019190002', '2017105567', '2015100831', '2016190001', '2017105082', '2019190004', '2017100720', '2016110103', '2016104887', '2016106606', '2016104791', '2018106545', '2019105195', '2018105165', '2013103569', '2018102167', '2016104618']

class PredictMoneyClass(encoder.Encoder_Money.MoneyClass):
    def get(self):
        # 賞金リスト
        self.xList = ["40000","16000","10000","6000","4000"]
class PredictHorseNumClass(encoder.Encoder_HorseNum.HorseNumClass):
    def get(self):
        # 出走する馬の頭数
        self.xList = [18]
class PredictCourseConditionClass(encoder.Encoder_CourseCondition.CourseConditionClass):
    def get(self):
        # コース状態
        # '良', '稍重', '重', '不良' のいずれか
        self.xList = '良'
class PredictCourseDistanceClass(encoder.Encoder_CourseDistance.CourseDistanceClass):
    def get(self):
        # コース長
        self.xList = [2400.0]
class PredictRaceStartTimeClass(encoder.Encoder_RaceStartTime.RaceStartTimeClass):
    def get(self):
        # 出走時刻
        self.xList = "15:40"
class PredictWeatherClass(encoder.Encoder_Weather.WeatherClass):
    def get(self):
        # 天気
        # '晴', '曇', '小雨', '雨', '小雪', '雪' のいずれか
        self.xList = '晴'
class PredictHorseAgeClass(encoder.Encoder_HorseAge.HorseAgeClass):
    def get(self):
        # レース開催日
        self.d0 = date(2022, 11, 27)

        # 誕生日をDBから取得
        bdList = []
        for horse_id in horse_id_list:
            bod = db_horse_bod(horse_id)
            bdList.append(bod)
        self.xList = bdList        
class PredictBurdenWeightClass(encoder.Encoder_BurdenWeight.BurdenWeightClass):
    def get(self):
        # 斤量
        self.xList = [55.0, 55.0, 57.0, 57.0, 55.0, 57.0, 55.0, 55.0, 57.0, 57.0, 57.0, 55.0, 57.0, 55.0, 57.0, 57.0, 55.0, 57.0]
class PredictPostPositionClass(encoder.Encoder_PostPosition.PostPositionClass):
    def get(self):
        # 枠番
        self.xList = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 7, 8, 8, 8]
class PredictJockeyClass(encoder.Encoder_Jockey.JockeyClass):
    def get(self):
        # jockey_id
        self.xList =  ['05498', '05339', '05585', '01117', '05464', '05366', 'a04a7', '05626', '01125', '00666', '01179', '01126', '01144', '01088', '05473', '01150', '05212', '01115']
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
        # blood_f の horse_id
        self.xList = horse_id_list
        self.col_num = len(self.xList)
class PredictLast3fClass(encoder.Encoder_Last3f.Last3fClass):
    def get(self):
        # race_id
        self.race_id = "202205050812"
        # horse_id
        self.xList = horse_id_list
