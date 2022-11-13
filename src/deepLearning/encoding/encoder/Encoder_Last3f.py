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

    def pad(self):
        # サイズの伸縮を行う
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            for i in range(adj_size):
                self.xList.append(0)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        np_list = np.array(self.xList)
        np_list = np_list / np.sum(np_list)
        self.xList = np_list.tolist()
