from Encoder_X import XClass
from debug import stream_hdl, file_hdl
import logging
import numpy as np

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("TimeClass"))

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

    def zscore(self, x, axis = None):
        xmean  = np.mean(x, axis=axis, keepdims=True, where = (x != 0))
        xstd   = np.std(x, axis=axis, keepdims=True, where = (x != 0))
        zscore = np.divide((x - xmean), xstd, out = np.zeros_like(x), where = (xstd != 0))
        return zscore

    def nrm(self):
        val = self.zscore(self.xList, axis=0)
        self.xList = val
