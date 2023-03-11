import numpy as np
import logging

from Encoder_X import XClass
from debug     import stream_hdl, file_hdl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("Last3fClass"))

class Last3fClass(XClass):

    def get(self):
        # 出走馬リスト取得
        self.xList = self.nf.db_race_list_horse_id(self.race_id)

    def fix(self):
        # 直前のレースのあがり3Fのリストを作成する
        last_3f_list = []
        for horse_id in self.xList:
            # 直前のレースIDを取得
            last_race_id = self.nf.db_race_last_race(self.race_id, horse_id, False)
            if len(last_race_id) == 0:
                # 直前に重賞レースに出走していないもしくはデータがない
                t = None
            else:
                # 直前のレースあがり3ハロンのタイムを取得
                t = self.nf.db_race_last_3f(last_race_id, horse_id)

            if (t is str) or (t is float):
                t = float(t)
            else:
                # 該当のレースがなかった
                t = float(0.0)

            last_3f_list.append(t)
            
        self.xList = last_3f_list

    def nrm(self):
        np_xList     = np.array(self.xList)
        np_sum_xList = np.sum(self.xList)

        # ans = np_xList / np_sum_xList
        # ただし、0除算する要素は0とする
        ans = np.divide(np_xList, np_sum_xList, out = np.zeros_like(np_xList), where = (np_sum_xList != 0))
        
        self.xList = ans.tolist()
