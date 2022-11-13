import numpy as np
from Encoder_X import XClass
from getFromDB import db_race_list_burden_weight

import logging
logger = logging.getLogger("BurdenWeightClass")

class BurdenWeightClass(XClass):

    def get(self):
        burdenWeightList = db_race_list_burden_weight(self.race_id)
        self.xList = burdenWeightList

    def pad(self):
        # ダミーデータ：平均値
        super().pad(np.mean(self.xList))

    def nrm(self):
        # 斤量の標準化
        # 一律60で割る
        SCALE_PARAMETER = 60
        n_weight_list = np.array(self.xList)
        n_weight_list = n_weight_list / SCALE_PARAMETER
        self.xList = n_weight_list.tolist()
