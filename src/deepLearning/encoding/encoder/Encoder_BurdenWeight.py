import numpy as np
from Encoder_X import XClass
from getFromDB import db_race_list_burden_weight

import logging
logger = logging.getLogger("BurdenWeightClass")

class BurdenWeightClass(XClass):

    def get(self):
        burdenWeightList = db_race_list_burden_weight(self.race_id)
        self.xList = burdenWeightList

    def fix(self):
        XClass.fix(self)

    def pad(self):
        # 斤量リスト拡張
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            # ダミーデータ：平均値
            mean_age = np.mean(self.xList)
            for i in range(adj_size):
                self.xList.append(mean_age)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        # 斤量の標準化
        # 一律60で割る
        SCALE_PARAMETER = 60
        n_weight_list = np.array(self.xList)
        n_weight_list = n_weight_list / SCALE_PARAMETER
        self.xList = n_weight_list.tolist()
