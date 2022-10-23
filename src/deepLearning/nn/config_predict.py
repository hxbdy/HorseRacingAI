# 学習済みパラメータからレース結果を予測する
# 学習済みパラメータを ./dst/trainedParam から読み込む
# 入力データ(予測したいレース情報)を手入力するファイル
# 入力されたレース情報から実際に推論を実行し、結果を出力するのは predict.py

from getFromDB import *
from encodingXClass import *

# 推測したいレース情報入力
# 菊花賞
# https://race.netkeiba.com/race/shutuba.html?race_id=202209040711
# ==========================================================================
class PredictHorseNumClass(HorseNumClass):
    def get(self):
        # 出走する馬の頭数
        self.xList = [18]
class PredictCourseConditionClass(CourseConditionClass):
    def get(self):
        # コース状態
        # '良', '稍重', '重', '不良' のいずれか
        self.xList = '良'
class PredictCourseDistanceClass(CourseDistanceClass):
    def get(self):
        # コース長
        self.xList = [3000.0]
class PredictRaceStartTimeClass(RaceStartTimeClass):
    def get(self):
        # 出走時刻
        self.xList = "15:40"
class PredictWeatherClass(WeatherClass):
    def get(self):
        # 天気
        # '晴', '曇', '小雨', '雨', '小雪', '雪' のいずれか
        self.xList = '晴'
class PredictHorseAgeClass(HorseAgeClass):
    def get(self):
        # 馬の誕生日
        self.xList = [
            date(2019, 2, 21),
            date(2019, 2, 3),
            date(2019, 4, 3),
            date(2019, 3, 23),
            date(2019, 4, 16),
            date(2019, 2, 28),
            date(2019, 2, 23),
            date(2019, 2, 16),
            date(2019, 4, 19),
            date(2019, 4, 8),
            date(2019, 2, 23),
            date(2019, 3, 25),
            date(2019, 4, 17),
            date(2019, 4, 1),
            date(2019, 3, 9),
            date(2019, 5, 15),
            date(2019, 4, 12),
            date(2019, 4, 4)
        ]
        # レース開催日
        self.d0 = date(2022, 10, 23)
class PredictBurdenWeightClass(BurdenWeightClass):
    def get(self):
        # 斤量
        self.xList = [57.0] * 18
class PredictPostPositionClass(PostPositionClass):
    def get(self):
        # 枠番
        self.xList = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 7, 8, 8, 8]
class PredictJockeyClass(JockeyClass):
    def get(self):
        # jockey_id
        self.xList =  ["01126","01030","01032","01095","00666","05203","01174","01091","01115","00732","01170","01088","01140","01075","01163","01154","01157","01014"]
class PredictCumPerformClass(CumPerformClass):
    def get(self):
        # horse_id
        horse_list = ["2019104476","2019102531","2019100109","2019104909","2019100603","2019101348","2019104937","2019100790","2019105654","2019102632","2019105556","2019100126","2019101507","2019104706","2019104762","2019105366","2019105346","2019105168"]
        self.getForCalcPerformInfo(horse_list)
class PredictBradleyTerryClass(BradleyTerryClass):
    def get(self):
        # horse_id
        self.xList = ["2019104476","2019102531","2019100109","2019104909","2019100603","2019101348","2019104937","2019100790","2019105654","2019102632","2019105556","2019100126","2019101507","2019104706","2019104762","2019105366","2019105346","2019105168"]
        self.col_num = len(self.xList)
class PredictUmamusumeClass(UmamusumeClass):
    def get(self):
        # horse_id
        self.xList = ["2019104476","2019102531","2019100109","2019104909","2019100603","2019101348","2019104937","2019100790","2019105654","2019102632","2019105556","2019100126","2019101507","2019104706","2019104762","2019105366","2019105346","2019105168"]
class PredictParentBradleyTerryClass(PredictBradleyTerryClass):
    def get(self):
        # blood_f の horse_id
        self.xList = ["2019104476","2019102531","2019100109","2019104909","2019100603","2019101348","2019104937","2019100790","2019105654","2019102632","2019105556","2019100126","2019101507","2019104706","2019104762","2019105366","2019105346","2019105168"]
        self.col_num = len(self.xList)
