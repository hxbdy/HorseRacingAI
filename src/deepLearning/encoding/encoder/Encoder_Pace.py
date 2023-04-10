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

        # NN学習では最大値が正解になるので、一位のタイムをゼロとして、それ以降の順位は差分で負の値を入れる
        np_total_pace_list = np.array(total_pace_list)
        np_total_pace_list = np_total_pace_list.reshape(-1, 2)

        m = np.nanmin(np_total_pace_list, axis=0) - np_total_pace_list
        self.xList = m.tolist()

        logger.debug(self.xList)

    def pad(self):
        nx = np.array(self.xList)
        nx = nx.reshape(-1, 2)
        nx_min = np.nanmin(nx, axis=0)

        logger.debug("nx_min = {0}".format(nx_min))
        super().pad(nx_min.tolist())

        rep = np.nan_to_num(self.xList)
        logger.debug("rep = {0}".format(rep))
        self.xList = rep.tolist()

    def nrm(self):
        # self.xList = [[first3f, last3f], ... ]
        np_pace_list = np.array(self.xList).reshape(-1, 2)

        # zscore
        ans_pace = self.zscore(np_pace_list, axis=0)

        # self.xList = [first3f1, first3f2, ... last3f1, last3f2, ...]
        self.xList = list(deepflatten(ans_pace.T.tolist()))
