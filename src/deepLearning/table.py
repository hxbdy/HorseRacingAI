import encoder

# 学習用データ生成条件
start_year_train = 1800 # 開始年
end_year_train   = 2020 # 終了年
limit_train      = -1   # 取得件数 -1 なら全件

# 学習データファイル名フォーマット
X_train_file_name = "x_train.pickle"
t_train_file_name = "t_train.pickle"
analysis_train_file_name = "analysis_train.pickle"

# テスト用データ生成条件
start_year_test = 2021 # 開始年
end_year_test   = 2021 # 終了年
limit_test      = -1   # 取得件数 -1 なら全件

# テストファイル名フォーマット
X_test_file_name = "x_test.pickle"
t_test_file_name = "t_test.pickle"
analysis_test_file_name = "analysis_test.pickle"

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
    encoder.Encoder_Jockey.JockeyClass,                          # Encoding takes too long
    encoder.Encoder_CumPerform.CumPerformClass,
    encoder.Encoder_BradleyTerry.BradleyTerryClass,
    encoder.Encoder_Umamusume.UmamusumeClass,
    encoder.Encoder_ParentBradleyTerry.ParentBradleyTerryClass,
    encoder.Encoder_Last3f.Last3fClass                           # Encoding takes too long
]

# 正解用テーブル
# !! 1つしか入れないで !!
tTbl = [
    encoder.Encoder_RankOneHot.RankOneHotClass # 1位のOne-Hot表現
    # encoder.Encoder_Margin.MarginClass   # 着差標準化
]
