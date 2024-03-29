import numpy as np
from iteration_utilities import deepflatten

from Encoder_X import XClass

class CornerPosClass(XClass):

    def get(self):
        self.xList = self.nf.db_race_list_horse_id(self.race_id)
        self.fix0()

    def fix0(self):
        # コーナーポジションは最大で4つあるので、4未満の時は0で埋める
        self.corner_pos_max = 4
        total_corner_list = []
        for horse_id in self.xList:
            # 直前のレースidを取得する
            last_race_id = self.nf.db_race_last_race(self.race_id, horse_id, False)
            self.logger.debug("(race_id = {0}, horse_id = {1}) -> last race_id = {2}".format(self.race_id, horse_id, last_race_id))

            # 直前の race_idが見つからなかった場合、今回のrace_idをそのまま使う
            if len(last_race_id) == 0:
                last_race_id = self.race_id

            # 直前のレースのコーナーポジションを取得する
            corner_pos_list = self.nf.db_corner_pos(last_race_id, horse_id)

            if corner_pos_list == None:
                # DB に記録されていない場合
                corner_pos_list = [0] * self.corner_pos_max

            total_corner_list.append(corner_pos_list)

        self.xList = total_corner_list
    
    def fix(self):
        pad_list = []
        for pos in self.xList:
            adj_size = self.corner_pos_max - len(pos)

            for i in range(adj_size):
                pos.append(0)

            pad_list.append(pos)
        self.xList = pad_list

    def pad(self):
        super().pad([0] * self.corner_pos_max)

    def nrm(self):
        # numpy / cupy 化
        np_xlist = np.array(self.xList).reshape(-1, self.corner_pos_max)

        # 最大値で割る
        # div_pos = np.max(np_xlist, axis=1).reshape(-1, 1)
        # ans_pos = np.divide(np_xlist, div_pos, out = np.zeros_like(np_xlist), where = (div_pos != 0))
        # self.xList = ans_pos.tolist()
        
        # 1列目を抽出
        # 最初の順位から各コーナーでどれだけ順位が変動したかがわかる
        # 他の馬の順位の変動の影響を受けない
        # div_pos = np_xlist[:, 0].reshape(-1, 1)

        np_xlist = self.zscore(np_xlist, axis=0, reverse=False)
        self.xList = np_xlist.tolist()

        self.logger.debug("self.xList = {0}".format(self.xList))
