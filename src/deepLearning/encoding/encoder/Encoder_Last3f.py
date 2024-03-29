

import numpy as np

from Encoder_X import XClass

class Last3fClass(XClass):

    def get(self):
        # 出走馬リスト取得
        self.xList = self.nf.db_race_list_horse_id(self.race_id)
        self.logger.debug("horse_id = {0}".format(self.xList))

    def fix(self):
        # 直前のレースのあがり3Fのリストを作成する
        last_3f_list = []
        for horse_id in self.xList:
            # 直前のレースIDを取得
            last_race_id = self.nf.db_race_last_race(self.race_id, horse_id, False)
            self.logger.debug("last_race_id = {0}".format(last_race_id))

            if (last_race_id == "None") or (len(last_race_id) == 0):
                # 直前にレースに出走していないもしくはデータがない
                t = float(0.0)
            else:
                # 直前のレースあがり3ハロンのタイムを取得
                t = self.nf.db_race_last_3f(last_race_id, horse_id)

            try:
                t = float(t)
            except (ValueError, TypeError):
                # 該当のレースがなかった
                t = float(0.0)               

            last_3f_list.append(t)

        self.logger.debug("last_3f_list = {0}".format(last_3f_list))
            
        self.xList = last_3f_list

    def nrm(self):
        np_xList     = np.array(self.xList)

        # zscore
        np_xList = self.zscore(np_xList, axis=-1)

        # ans = np_xList / np_sum_xList
        # ただし、0除算する要素は0とする
        # np_sum_xList = np.sum(self.xList)
        # ans = np.divide(np_xList, np_sum_xList, out = np.zeros_like(np_xList), where = (np_sum_xList != 0))
        
        self.xList = np_xList.tolist()
