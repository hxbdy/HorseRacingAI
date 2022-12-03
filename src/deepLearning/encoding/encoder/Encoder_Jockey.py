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
        # 騎手のrace_id開催年までの総出場回数を求める
        # lower_year年1月1日からupper_year年12月31日までの騎乗回数を求める
        # (upper_year - 5) <= 取得する期間 <= (upper_year)
        jockeyIDList = self.xList
        for i in range(len(jockeyIDList)):
            upper_year = "{0:4d}".format(int(self.race_id[0:4]) - 1)
            lower_year = "{0:4d}".format(int(upper_year) - 5)
            cnt = db_race_cnt_jockey(jockeyIDList[i], lower_year, upper_year)
            logger.debug("jockey_id = {0}, lower_year = {1}, upper_year = {2}, cnt = {3}".format(jockeyIDList[i], lower_year, upper_year, cnt))
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
