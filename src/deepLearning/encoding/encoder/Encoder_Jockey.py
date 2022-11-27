from Encoder_X import XClass
from getFromDB import db_race_list_jockey, db_race_cnt_jockey
import numpy as np

from debug import stream_hdl, file_hdl

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("JockeyClass"))

class JockeyClass(XClass):

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
        # ダミーデータ：出場回数50を追加．
        super().pad(50)

    def nrm(self):
        # 騎手標準化
        # 最高値ですべてを割る
        njockeyList = np.array(self.xList)
        maxJockey = np.max(njockeyList)
        njockeyList = njockeyList / maxJockey
        self.xList = njockeyList.tolist()
