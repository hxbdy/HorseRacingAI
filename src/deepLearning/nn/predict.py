# 推測する
# 予測したいレース情報は src\deepLearning\nn\config_predict.py で入力してください
# > python ./src/deepLearning/nn/predict.py

import configparser
import pickle
import numpy as np

from iteration_utilities import deepflatten

import encoder
import TwoLayerNet
from RaceInfo import RaceInfo
from encoding_common   import encoding_load
from getFromDB         import db_horse_bod, db_horse_father
from make_RaceInfo import raceinfo_by_raceID

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
        self.xList = tmp_param.prize
class PredictHorseNumClass(encoder.Encoder_HorseNum.HorseNumClass):
    def get(self):
        # 出走する馬の頭数
        self.xList = [tmp_param.horse_num]
class PredictCourseConditionClass(encoder.Encoder_CourseCondition.CourseConditionClass):
    def get(self):
        # コース状態
        # '良', '稍重', '重', '不良' のいずれか
        self.xList = tmp_param.course_condition
class PredictCourseDistanceClass(encoder.Encoder_CourseDistance.CourseDistanceClass):
    def get(self):
        # コース長
        self.xList = tmp_param.distance
class PredictRaceStartTimeClass(encoder.Encoder_RaceStartTime.RaceStartTimeClass):
    def get(self):
        # 出走時刻
        self.xList = tmp_param.start_time
class PredictWeatherClass(encoder.Encoder_Weather.WeatherClass):
    def get(self):
        # 天気
        # '晴', '曇', '小雨', '雨', '小雪', '雪' のいずれか
        self.xList = tmp_param.weather
class PredictHorseAgeClass(encoder.Encoder_HorseAge.HorseAgeClass):
    def get(self):
        # レース開催日
        self.d0 = tmp_param.date

        # 誕生日をDBから取得
        bdList = []
        for horse_id in tmp_param.horse_id:
            bod = db_horse_bod(horse_id)
            bdList.append(bod)
        self.xList = bdList        
class PredictBurdenWeightClass(encoder.Encoder_BurdenWeight.BurdenWeightClass):
    def get(self):
        # 斤量
        self.xList = tmp_param.burden_weight
class PredictPostPositionClass(encoder.Encoder_PostPosition.PostPositionClass):
    def get(self):
        # 枠番
        self.xList = tmp_param.post_position
class PredictJockeyClass(encoder.Encoder_Jockey.JockeyClass):
    def get(self):
        # jockey_id
        self.xList = tmp_param.jockey_id
        # race_id
        self.race_id = tmp_param.race_id
class PredictCumPerformClass(encoder.Encoder_CumPerform.CumPerformClass):
    def get(self):
        # horse_id
        self.getForCalcPerformInfo(tmp_param.horse_id)
class PredictBradleyTerryClass(encoder.Encoder_BradleyTerry.BradleyTerryClass):
    def get(self):
        # horse_id
        self.xList = tmp_param.horse_id
        self.col_num = len(self.xList)
class PredictUmamusumeClass(encoder.Encoder_Umamusume.UmamusumeClass):
    def get(self):
        # horse_id
        self.xList = tmp_param.horse_id
class PredictParentBradleyTerryClass(encoder.Encoder_ParentBradleyTerry.ParentBradleyTerryClass):
    def get(self):
        # horse_id
        childList = tmp_param.horse_id
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
        self.race_id = tmp_param.race_id
        # horse_id
        self.xList = tmp_param.horse_id

def prob_win(value_list):
    # 勝つ可能性 (ロジットモデル)
    ls = np.array(value_list)
    ls_sorted_idx = np.argsort(-ls) # 降順のソート
    ls_sorted = ls[ls_sorted_idx]
    prob = np.exp(ls_sorted)/sum(np.exp(ls_sorted)) # 確率計算
    prob_disp = ["{:.3f}".format(i) for i in prob] # 表示桁数を制限
    
    print(["{:^5d}".format(i) for i in ls_sorted_idx+1])
    print(prob_disp)
    #return list(ls_sorted_idx), prob

def read_RaceInfo(race_id = ""):
    """推測するレースのRaceInfoオブジェクトを読み込む
    race_id: 指定した場合、データベースから読込。無指定ならばpickleを読込
    """
    if race_id == "":
        # TODO: 読み込みに失敗したとき、情報をスクレイピングしておく旨を表示して終了する対応
        with open(path_tmp, 'rb') as f:
            tmp_param: RaceInfo = pickle.load(f)
        return tmp_param
    else:
        param = raceinfo_by_raceID(str(race_id))
        return param


if __name__ == "__main__":
    # パス読み込み
    config = configparser.ConfigParser()
    config.read('./src/path.ini', 'UTF-8')
    path_tmp = config.get('common', 'path_tmp')

    #tmp_param = read_RaceInfo('202205050812') # race_id 指定(データベースから)
    tmp_param = read_RaceInfo() # 当日推測用(pickleファイルから)

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
    x_train, t_train, x_test, t_test = encoding_load()

    # 推測用エンコード
    x = []
    for func in predict_XTbl:
        # インスタンス生成
        predict = func()
        x.append(predict.adj())
    x = np.array(list(deepflatten(x))).reshape(1, -1)

    # 保存済みパラメータ読み込み
    net = TwoLayerNet.TowLayerNet(x_train.shape[1], 40, t_train.shape[1])
    net.loadParam("newest")

    # 推測
    y = list(deepflatten(net.predict(x)))
    prob_win(y)
