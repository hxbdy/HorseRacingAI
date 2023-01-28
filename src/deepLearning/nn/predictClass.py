import encoder

# ==========================================================================
# 親クラスXClassの変数としてレース情報は設定済みの前提
# ==========================================================================
class PredictMoneyClass(encoder.Encoder_Money.MoneyClass):
    def get(self):
        # 賞金リスト
        self.xList = self.race_info.prize
class PredictHorseNumClass(encoder.Encoder_HorseNum.HorseNumClass):
    def get(self):
        # 出走する馬の頭数
        self.xList = self.race_info.horse_num
class PredictCourseConditionClass(encoder.Encoder_CourseCondition.CourseConditionClass):
    def get(self):
        # コース状態
        # '良', '稍重', '重', '不良' のいずれか
        self.xList = self.race_info.course_condition
class PredictCourseDistanceClass(encoder.Encoder_CourseDistance.CourseDistanceClass):
    def get(self):
        # コース長
        self.xList = self.race_info.distance
class PredictRaceStartTimeClass(encoder.Encoder_RaceStartTime.RaceStartTimeClass):
    def get(self):
        # 出走時刻
        self.xList = self.race_info.start_time
class PredictWeatherClass(encoder.Encoder_Weather.WeatherClass):
    def get(self):
        # 天気
        # '晴', '曇', '小雨', '雨', '小雪', '雪' のいずれか
        self.xList = self.race_info.weather
class PredictHorseAgeClass(encoder.Encoder_HorseAge.HorseAgeClass):
    def get(self):
        from getFromDB import db_horse_bod
        # レース開催日
        self.d0 = self.race_info.date
        # 誕生日をDBから取得
        bdList = []
        for horse_id in self.race_info.horse_id:
            bod = db_horse_bod(horse_id)
            bdList.append(bod)
        self.xList = bdList        
class PredictBurdenWeightClass(encoder.Encoder_BurdenWeight.BurdenWeightClass):
    def get(self):
        # 斤量
        self.xList = self.race_info.burden_weight
class PredictPostPositionClass(encoder.Encoder_PostPosition.PostPositionClass):
    def get(self):
        # 枠番
        self.xList = self.race_info.post_position
class PredictJockeyClass(encoder.Encoder_Jockey.JockeyClass):
    def get(self):
        # jockey_id
        self.xList = self.race_info.jockey_id
        # race_id
        self.race_id = self.race_info.race_id
class PredictCumPerformClass(encoder.Encoder_CumPerform.CumPerformClass):
    def get(self):
        # horse_id
        self.getForCalcPerformInfo(self.race_info.horse_id)
class PredictBradleyTerryClass(encoder.Encoder_BradleyTerry.BradleyTerryClass):
    def get(self):
        # horse_id
        self.xList = self.race_info.horse_id
        self.col_num = len(self.xList)
class PredictUmamusumeClass(encoder.Encoder_Umamusume.UmamusumeClass):
    def get(self):
        # horse_id
        self.xList = self.race_info.horse_id
class PredictParentBradleyTerryClass(encoder.Encoder_ParentBradleyTerry.ParentBradleyTerryClass):
    def get(self):
        from getFromDB import db_horse_father
        # horse_id
        childList = self.race_info.horse_id
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
        self.race_id = self.race_info.race_id
        # horse_id
        self.xList = self.race_info.horse_id
class PredictHorseWeight(encoder.Encoder_HorseWeight.HorseWeightClass):
    def get(self):
        # 馬体重リスト
        self.xList = self.race_info.horse_weight
class PredictCornerPos(encoder.Encoder_CornerPos.CornerPosClass):
    def get(self):
        # horse_id
        self.xList = self.race_info.horse_id
        self.fix0()
# ==========================================================================

# 推論時の入力用テーブル
predict_XTbl = [
    PredictMoneyClass,
    PredictHorseNumClass,
    PredictCourseConditionClass,
    PredictCourseDistanceClass,
    PredictRaceStartTimeClass,
    PredictWeatherClass,
    PredictHorseAgeClass,
    PredictBurdenWeightClass,
    PredictPostPositionClass,
    PredictJockeyClass,
    PredictCumPerformClass,
    PredictBradleyTerryClass,
    PredictUmamusumeClass,
    PredictParentBradleyTerryClass,
    PredictLast3fClass,
    PredictHorseWeight,
    PredictCornerPos
]
