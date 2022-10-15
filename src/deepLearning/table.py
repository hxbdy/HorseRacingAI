from encodingXClass import *
from config_predict import *

# 学習用データ生成条件
start_year_train = 1800
end_year_train   = 2020
limit_train      = -1

# 学習データファイル名フォーマット
X_train_file_name = "X_{0}-{1}-{2}.pickle".format(start_year_train, end_year_train, limit_train)
t_train_file_name = "t_{0}-{1}-{2}.pickle".format(start_year_train, end_year_train, limit_train)
analysis_train_file_name = "analysis_{0}-{1}-{2}.pickle".format(start_year_train, end_year_train, limit_train)

# テスト用データ生成条件
start_year_test = 2021
end_year_test   = 2021
limit_test      = -1

# テストファイル名フォーマット
X_test_file_name = "X_{0}-{1}-{2}.pickle".format(start_year_test, end_year_test, limit_test)
t_test_file_name = "t_{0}-{1}-{2}.pickle".format(start_year_test, end_year_test, limit_test)
analysis_test_file_name = "analysis_{0}-{1}-{2}.pickle".format(start_year_test, end_year_test, limit_test)

# 学習時の入力用テーブル
XTbl = [
    HorseNumClass,
    CourseConditionClass,
    CourseDistanceClass,
    RaceStartTimeClass,
    WeatherClass,
    HorseAgeClass,
    BurdenWeightClass,
    PostPositionClass,
    JockeyClass,
    CumPerformClass,
    BradleyTerryClass,
    UmamusumeClass,
    ParentBradleyTerryClass,
]

# 生成済み入力用テーブルから一部挿げ替えを行えるテーブル
chgXTbl = [
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
]

# 推論時の入力用テーブル
predict_XTbl = [
    PredictHorseNumClass,
    PredictCourseConditionClass,
    PredictCourseDistanceClass,
    PredictRaceStartTimeClass,
    PredictWeatherClass,
    PredictHorseAgeClass,
    PredictBurdenWeightClass,
    PredictPostPositionClass,
    PredictJockeyClass,
    PredictBradleyTerryClass,
    PredictUmamusumeClass,
    PredictParentBradleyTerryClass,
]

# 正解用テーブル
# !! 1つしか入れないで !!
tTbl = [
    RankOneHotClass # 1位のOne-Hot表現
    # MarginClass   # 着差標準化
]

# 生成済み教師テーブルから一部挿げ替えを行えるテーブル
# !! 1つしか入れないで !!
chgtTbl = [
    None
]
