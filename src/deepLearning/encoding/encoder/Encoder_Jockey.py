

import numpy as np

from Encoder_X import XClass

class JockeyClass(XClass):

    def get(self):
        jockeyIDList = self.nf.db_race_list_jockey(self.race_id)
        self.xList = jockeyIDList

    def fix(self):
        # 騎手のrace_id開催年までの総出場回数を求める
        # lower_year年1月1日からupper_year年12月31日までの騎乗回数を求める
        # (upper_year - 5) <= 取得する期間 <= (upper_year)
        jockeyIDList = self.xList
        for i in range(len(jockeyIDList)):
            upper_year = "{0:4d}".format(int(self.race_id[0:4]))
            lower_year = "{0:4d}".format(int(upper_year) - 5)
            cnt = self.nf.db_race_cnt_jockey(jockeyIDList[i], lower_year, upper_year)
            self.logger.debug("jockey_id = {0}, lower_year = {1}, upper_year = {2}, cnt = {3}".format(jockeyIDList[i], lower_year, upper_year, cnt))
            jockeyIDList[i] = cnt
        self.xList = jockeyIDList

    def pad(self):
        # 騎手ダミーデータ挿入
        # ダミーデータ：出場回数50を追加．
        # super().pad(50)
        super().pad(0)

    def nrm(self):
        # 騎手標準化
        njockeyList = np.array(self.xList)
        
        # 最高値ですべてを割る
        # maxJockey = np.max(njockeyList)
        # self.logger.debug("njockeyList = {0}, maxJockey = {1}".format(njockeyList, maxJockey))
        # njockeyList = njockeyList / maxJockey
        # self.xList = njockeyList.tolist()
        
        # zscore
        njockeyList = self.zscore(njockeyList, axis=-1, reverse=False)
        self.xList = njockeyList.tolist()
