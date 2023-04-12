import logging
import numpy as np

from iteration_utilities import deepflatten

from Encoder_X import XClass
from debug     import stream_hdl, file_hdl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("PaceClass"))

class PaceClass(XClass):

    def get(self):
        # 出走する馬一覧取得
        self.xList = self.nf.db_race_list_horse_id(self.race_id)
    
    def fix(self):
        total_pace_list = []
        for horse_id in self.xList:
            # 直前のレースidを取得する
            last_race_id = self.nf.db_race_last_race(self.race_id, horse_id, False)
            logger.debug("(race_id = {0}, horse_id = {1}) -> last race_id = {2}".format(self.race_id, horse_id, last_race_id))

            # 直前の race_idが見つからなかった場合、今回のrace_idをそのまま使う
            if len(last_race_id) == 0:
                last_race_id = self.race_id

            # 直前の重賞レースのコーナーポジションを取得する
            pace_list = self.nf.db_pace(last_race_id, horse_id)

            if pace_list == None:
                # DB に記録されていない場合
                pace_list = [np.nan, np.nan]

            total_pace_list.append(pace_list)

        self.xList = total_pace_list

    def pad(self):
        nx = np.array(self.xList)
        nx = nx.reshape(-1, 2)
        
        # 最大値(ビリ)のペースで馬番を18番まで埋める
        nx_max = np.nanmax(nx, axis=0, out=np.zeros_like([1, 2]))
        super().pad(nx_max.tolist())
        nx = np.array(self.xList)

        # 取得できなった値も最大値で埋める
        np.nan_to_num(nx[:, 0], nan=nx_max[0], copy=False)
        np.nan_to_num(nx[:, 1], nan=nx_max[1], copy=False)

        self.xList = nx.tolist()

    def nrm(self):
        # self.xList = [[first3f, last3f], ... ]
        np_pace_list = np.array(self.xList).reshape(-1, 2)

        # zscore
        ans_pace = self.zscore(np_pace_list, axis=0, reverse=True)

        # self.xList = [first3f1, first3f2, ... last3f1, last3f2, ...]
        self.xList = list(deepflatten(ans_pace.T.tolist()))
