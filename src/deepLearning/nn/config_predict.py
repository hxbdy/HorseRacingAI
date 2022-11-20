# 学習済みパラメータからレース結果を予測する
# 学習済みパラメータを dst\trainedParam\newest から読み込む
# 入力データ(予測したいレース情報)を手入力してください
# 入力されたレース情報から実際に推論を実行し、結果を出力するのは src\deepLearning\nn\predict.py

from datetime import date

import encoder

# 推測したいレース情報入力
# マイルCS
# https://race.netkeiba.com/race/shutuba.html?race_id=202209050611&rf=top_pickup
# 結果
# https://race.netkeiba.com/special/index.html?id=0119&rf=top_pickup
# ==========================================================================
class PredictMoneyClass(encoder.Encoder_Money.MoneyClass):
    def get(self):
        # 賞金リスト
        self.xList = ["18000","7200","4500","2700","1800"]
class PredictHorseNumClass(encoder.Encoder_HorseNum.HorseNumClass):
    def get(self):
        # 出走する馬の頭数
        self.xList = [17]
class PredictCourseConditionClass(encoder.Encoder_CourseCondition.CourseConditionClass):
    def get(self):
        # コース状態
        # '良', '稍重', '重', '不良' のいずれか
        self.xList = '良'
class PredictCourseDistanceClass(encoder.Encoder_CourseDistance.CourseDistanceClass):
    def get(self):
        # コース長
        self.xList = [1600.0]
class PredictRaceStartTimeClass(encoder.Encoder_RaceStartTime.RaceStartTimeClass):
    def get(self):
        # 出走時刻
        self.xList = "15:40"
class PredictWeatherClass(encoder.Encoder_Weather.WeatherClass):
    def get(self):
        # 天気
        # '晴', '曇', '小雨', '雨', '小雪', '雪' のいずれか
        self.xList = '曇'
class PredictHorseAgeClass(encoder.Encoder_HorseAge.HorseAgeClass):
    def get(self):
        # 馬の誕生日
        self.xList = [
            date(2019, 2, 20),
            date(2017, 4, 16),
            date(2018, 1, 29),
            date(2018, 3, 23),
            date(2017, 1, 23),
            date(2018, 3, 8),
            date(2018, 5, 18),
            date(2017, 1, 31),
            date(2019, 1, 7),
            date(2019, 3, 7),
            date(2018, 3, 28),
            date(2018, 2, 12),
            date(2017, 3, 6),
            date(2012, 3, 4),
            date(2019, 2, 22),
            date(2016, 3, 18),
            date(2017, 2, 10),
        ]
        # レース開催日
        self.d0 = date(2022, 11, 20)
class PredictBurdenWeightClass(encoder.Encoder_BurdenWeight.BurdenWeightClass):
    def get(self):
        # 斤量
        self.xList = [56.0, 57.0, 57.0, 57.0, 57.0, 55.0, 57.0, 55.0, 56.0, 56.0, 57.0, 57.0, 57.0, 57.0, 56.0, 57.0, 57.0]
class PredictPostPositionClass(encoder.Encoder_PostPosition.PostPositionClass):
    def get(self):
        # 枠番
        self.xList = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 8]
class PredictJockeyClass(encoder.Encoder_Jockey.JockeyClass):
    def get(self):
        # jockey_id
        self.xList =  ['00660', '01122', '01102', '05339', '05366', '01095', '01014', '01174', '05473', '05585', '01126', '01163', '00666', '01093', '01088', '01166', '01032']
class PredictCumPerformClass(encoder.Encoder_CumPerform.CumPerformClass):
    def get(self):
        # horse_id
        horse_list = ['2019100965', '2017101429', '2018104963', '2018110007', '2017105327', '2018105233', '2018104576', '2017110144', '2019105318', '2019104462', '2018100382', '2018105192', '2017104685', '2012103405', '2019103034', '2016102692', '2017104719']
        self.getForCalcPerformInfo(horse_list)
class PredictBradleyTerryClass(encoder.Encoder_BradleyTerry.BradleyTerryClass):
    def get(self):
        # horse_id
        self.xList = ['2019100965', '2017101429', '2018104963', '2018110007', '2017105327', '2018105233', '2018104576', '2017110144', '2019105318', '2019104462', '2018100382', '2018105192', '2017104685', '2012103405', '2019103034', '2016102692', '2017104719']
        self.col_num = len(self.xList)
class PredictUmamusumeClass(encoder.Encoder_Umamusume.UmamusumeClass):
    def get(self):
        # horse_id
        self.xList = ['2019100965', '2017101429', '2018104963', '2018110007', '2017105327', '2018105233', '2018104576', '2017110144', '2019105318', '2019104462', '2018100382', '2018105192', '2017104685', '2012103405', '2019103034', '2016102692', '2017104719']
class PredictParentBradleyTerryClass(encoder.Encoder_ParentBradleyTerry.ParentBradleyTerryClass):
    def get(self):
        # blood_f の horse_id
        self.xList = ['2019100965', '2017101429', '2018104963', '2018110007', '2017105327', '2018105233', '2018104576', '2017110144', '2019105318', '2019104462', '2018100382', '2018105192', '2017104685', '2012103405', '2019103034', '2016102692', '2017104719']
        self.col_num = len(self.xList)
class PredictLast3fClass(encoder.Encoder_Last3f.Last3fClass):
    def get(self):
        # race_id
        self.race_id = "202209050611"
        # horse_id
        self.xList = ['2019100965', '2017101429', '2018104963', '2018110007', '2017105327', '2018105233', '2018104576', '2017110144', '2019105318', '2019104462', '2018100382', '2018105192', '2017104685', '2012103405', '2019103034', '2016102692', '2017104719']
