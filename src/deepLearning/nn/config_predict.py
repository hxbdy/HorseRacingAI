# 学習済みパラメータからレース結果を予測する
# 学習済みパラメータを ./dst/trainedParam から読み込む
# 入力データ(予測したいレース情報)を手入力するファイル
# 入力されたレース情報から実際に推論を実行し、結果を出力するのは predict.py

from getFromDB import *
from encodingXClass import *

# 推測したいレース情報入力
# ==========================================================================
class PredictHorseNumClass(HorseNumClass):
    def get(self):
        # 出走する馬の頭数
        self.xList = [23]

class PredictCourseConditionClass(CourseConditionClass):
    def get(self):
        # コース状態
        # '良', '稍重', '重', '不良' のいずれか
        self.xList = '良'
        
class PredictCourseDistanceClass(CourseDistanceClass):
    def get(self):
        # コース長
        self.xList = [1600.0]
class PredictRaceStartTimeClass(RaceStartTimeClass):
    def get(self):
        # 出走時刻
        self.xList = "15:35"
class PredictWeatherClass(WeatherClass):
    def get(self):
        # 天気
        # '晴', '曇', '小雨', '雨', '小雪', '雪' のいずれか
        self.xList = '晴'
class PredictHorseAgeClass(HorseAgeClass):
    def get(self):
        # 馬の誕生日
        self.xList = [date(1998,6,25), date(2003, 3, 12)]
class PredictBurdenWeightClass(BurdenWeightClass):
    def get(self):
        # 斤量
        self.xList = [60.0, 50.0]
class PredictPostPositionClass(PostPositionClass):
    def get(self):
        # 枠番
        self.xList = [1, 2]
class PredictJockeyClass(JockeyClass):
    def get(self):
        # jockey_id
        self.xList = ['00586', '00298']
class PredictCumPerformClass(CumPerformClass):
    def get(self):
        # horse_id
        horse_list = ["1983103914", "1983104782"]
        self.getForCalcPerformInfo(horse_list)
class PredictBradleyTerryClass(BradleyTerryClass):
    def get(self):
        # horse_id
        self.xList = ["1983103914", "1983104782"]
        self.col_num = len(self.xList)
class PredictUmamusumeClass(UmamusumeClass):
    def get(self):
        # horse_id
        self.xList = ["1983103914", "1983104782"]

class PredictParentBradleyTerryClass(PredictBradleyTerryClass):
    def get(self):
        # blood_f の horse_id
        self.xList = ["1983103914", "1983104782"]
        self.col_num = len(self.xList)

# レース開催日
d0 = date(2022, 9, 1)

# ==========================================================================
