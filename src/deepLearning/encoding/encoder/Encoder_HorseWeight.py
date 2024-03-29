

import re
import numpy as np

from iteration_utilities import deepflatten

from Encoder_X import XClass

class HorseWeightClass(XClass):

    def get(self):
        weight_list = self.nf.db_race_horse_weight(self.race_id)
        self.xList = weight_list
    
    def fix(self):
        weight_list = []
        for row in self.xList:
            # row = 530(+5)
            self.logger.debug("raw = {0}".format(row))

            try:
                # base = "530"
                # delta = "+5"
                base, delta = re.findall("[\+\-]*\d+", row) 
            except (ValueError, TypeError):
                # raw = 計不, None
                self.logger.debug("failed to get horse_weight race_id = {0}".format(self.race_id))
                # 競争馬平均kg
                base = 470
                delta = 0

            weight_list.append([float(base), float(delta)])

        self.xList = weight_list

    def pad(self):
        super().pad([470.0, 0.0])

    def nrm(self):
        # self.xList = [[馬体重, 増減], ... ]
        np_weight_list = np.array(self.xList).reshape(-1, 2)

        np_weight_list = self.zscore(np_weight_list, axis=0, reverse=False)
        self.xList = list(deepflatten(np_weight_list.tolist()))

        # 馬体重を最大値で割る
        # max_weight = np.max(np.abs(np_weight_list), axis=0)
        # ans_weight = np.divide(np_weight_list, max_weight, out = np.zeros_like(np_weight_list), where = (max_weight != 0))

        # self.xList = [馬体重1, 馬体重2, ... 増減1, 増減2, ...]
        # self.xList = list(deepflatten(ans_weight.T.tolist()))
