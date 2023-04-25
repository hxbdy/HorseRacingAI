from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import numpy as np
from Encoder_X import XClass

class TimeClass(XClass):

    def get(self):
        # 出走する馬一覧取得
        horse_id_list = self.nf.db_race_list_horse_id(self.race_id)
        
        # race_info テーブルからその馬の走破タイムを取得
        time_list = []
        for horse_id in horse_id_list:
            time_list.append(self.nf.db_race_time(self.race_id, horse_id))
        
        self.xList = time_list
        logger.debug(self.xList)

    def pad(self):
        # 最下位のタイムで埋める
        super().pad(max(self.xList))

    def nrm(self):
        np_xList = np.array(self.xList)
        val = self.zscore(np_xList, axis=-1, reverse=True)
        self.xList = val.tolist()
