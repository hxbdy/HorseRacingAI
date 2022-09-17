import sys
import pathlib

# commonフォルダ内読み込みのため
deepLearning_dir = pathlib.Path(__file__).parent
src_dir = deepLearning_dir.parent
root_dir = src_dir.parent
dir_lst = [deepLearning_dir, src_dir, root_dir]
for dir_name in dir_lst:
    if str(dir_name) not in sys.path:
        sys.path.append(str(dir_name))

from common.XClass import *
from config_predict import *

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
    CumPerformClass
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
    PredictCumPerformClass
]

# 正解用テーブル
# !! 1つしか入れないで !!
tTbl = [
    RankOneHotClass # 1位のOne-Hot表現
    # MarginClass   # 着差標準化
]
