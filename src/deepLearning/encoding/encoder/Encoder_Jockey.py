from Encoder_X import XClass
from getFromDB import db_race_list_jockey, db_race_cnt_jockey
import numpy as np

import logging
logger = logging.getLogger(__name__)

class JockeyClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        jockeyIDList = db_race_list_jockey(self.race_id)
        self.xList = jockeyIDList

    def fix(self):
        # 騎手の総出場回数を求める
        jockeyIDList = self.xList
        for i in range(len(jockeyIDList)):
            cnt = db_race_cnt_jockey(jockeyIDList[i])
            jockeyIDList[i] = cnt
        self.xList = jockeyIDList

    def pad(self):
        # 騎手ダミーデータ挿入
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            # ダミーデータ：出場回数50を追加．
            for i in range(adj_size):
                self.xList.append(50)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        # 騎手標準化
        # 最高値ですべてを割る
        njockeyList = np.array(self.xList)
        maxJockey = np.max(njockeyList)
        njockeyList = njockeyList / maxJockey
        self.xList = njockeyList.tolist()

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList
