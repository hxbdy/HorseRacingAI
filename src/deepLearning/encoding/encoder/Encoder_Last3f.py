from Encoder_X import XClass
from getFromDB import db_race_list_horse_id, db_race_last_3f, db_race_last_race
import numpy as np

import logging
logger = logging.getLogger("Last3fClass")

class Last3fClass(XClass):

    def get(self):
        # 出走馬リスト取得
        self.xList = db_race_list_horse_id(self.race_id)

    def fix(self):
        # 直前のレースのあがり3Fのリストを作成する
        last_3f_list = []
        for horse_id in self.xList:
            # 直前のレースIDを取得
            last_race_id = db_race_last_race(self.race_id, horse_id)

            # 直前のレースあがり3ハロンのタイムを取得
            t = db_race_last_3f(last_race_id, horse_id)
            if (t == None) or (t.isspace()):
                # 空白文字のみだった -> 該当のレースがなかった
                t = float(0.0)
                
            else:
                t = float(t)

            last_3f_list.append(t)
            
        self.xList = last_3f_list

    def nrm(self):
        np_xList     = np.array(self.xList)
        np_sum_xList = np.sum(self.xList)

        # ans = np_xList / np_sum_xList
        # ただし、0除算する要素は0とする
        ans = np.divide(np_xList, np_sum_xList, out = np.zeros_like(np_xList), where = (np_sum_xList != 0))
        
        self.xList = ans.tolist()
