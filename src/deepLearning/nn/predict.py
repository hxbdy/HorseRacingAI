# 推測する
# 予測したいレース情報は src\deepLearning\nn\config_predict.py で入力してください
# > python ./src/deepLearning/nn/predict.py

import configparser
import pickle
import numpy as np
from datetime import date

from iteration_utilities import deepflatten

import encoder
import TwoLayerNet
from netkeiba_scraping import RaceInfo
from encoding_common   import encoding_load
from getFromDB         import db_horse_bod, db_horse_father

# 推測したいレース情報入力
# ジャパンカップ
# https://race.netkeiba.com/race/shutuba.html?race_id=202205050812&rf=top_pickup
# 結果
# 
# ==========================================================================


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


if __name__ == "__main__":
    # パス読み込み
    config = configparser.ConfigParser()
    config.read('./src/path.ini', 'UTF-8')
    path_learningList = config.get('nn', 'path_learningList')
    path_tmp          = config.get('common', 'path_tmp')

    with open(path_tmp, 'rb') as f:
        tmp_param = pickle.load(f)

    # レース当日入力フィールド
    # horse_id
    horse_id_list = tmp_param.horse_id
    # 賞金リスト
    money_list = tmp_param.prize
    # 出走する馬の頭数
    horse_num = [len(tmp_param.horse_id)]
    # コース状態
    # '良', '稍重', '重', '不良' のいずれか
    course_condition = tmp_param.course_condition
    # コース長
    course_distance = tmp_param.distance
    # 出走時刻
    start_time = tmp_param.start_time
    # 天気
    # '晴', '曇', '小雨', '雨', '小雪', '雪' のいずれか
    weather = tmp_param.weather
    # レース開催日
    race_date = date(2022, 11, 27)
    # 斤量
    burden_weight = tmp_param.burden_weight
    # 枠番
    post_position = tmp_param.post_position
    # 騎手ID
    jockey_id_list =  tmp_param.jockey_id
    # レースID
    today_race_id = "202205050812"

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
        PredictLast3fClass
    ]

    # 行列サイズ取得のため学習データの読込
    (x_train, t_train), (x_test, t_test) = encoding_load(path_learningList)

    # 推測用エンコード
    x = []
    for func in predict_XTbl:
        # インスタンス生成
        predict = func()
        x.append(predict.adj())
    x = np.array(list(deepflatten(x))).reshape(1, -1)

    # 保存済みパラメータ読み込み
    net = TwoLayerNet.TowLayerNet(x_train.shape[1], 40, t_train.shape[1])
    net.loadParam()

    # 推測
    y = net.predict(x)
    print("y = ", y)

    pre = np.argsort(y) + 1

    # ソート済みの各馬番が1位になる確率
    print("predict = ", pre[0][::-1])
