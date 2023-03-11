import encoder

# 学習時の入力用テーブル
XTbl = [
    encoder.Encoder_Money.MoneyClass,
    encoder.Encoder_HorseNum.HorseNumClass,
    encoder.Encoder_CourseCondition.CourseConditionClass,
    encoder.Encoder_CourseDistance.CourseDistanceClass,
    encoder.Encoder_RaceStartTime.RaceStartTimeClass,
    encoder.Encoder_Weather.WeatherClass,
    encoder.Encoder_HorseAge.HorseAgeClass,
    encoder.Encoder_BurdenWeight.BurdenWeightClass,
    encoder.Encoder_PostPosition.PostPositionClass,
    encoder.Encoder_Jockey.JockeyClass,
    encoder.Encoder_CumPerform.CumPerformClass,
    encoder.Encoder_BradleyTerry.BradleyTerryClass,
    encoder.Encoder_Umamusume.UmamusumeClass,
    encoder.Encoder_ParentBradleyTerry.ParentBradleyTerryClass,
    encoder.Encoder_Last3f.Last3fClass,
    encoder.Encoder_HorseWeight.HorseWeightClass,
    encoder.Encoder_CornerPos.CornerPosClass,
    encoder.Encoder_Pace.PaceClass
]

# 正解用テーブル
# !! 1つしか入れないで !!
tTbl = [
    encoder.Encoder_RankOneHot.RankOneHotClass # 1位のOne-Hot表現
    # encoder.Encoder_Margin.MarginClass   # 着差標準化
]