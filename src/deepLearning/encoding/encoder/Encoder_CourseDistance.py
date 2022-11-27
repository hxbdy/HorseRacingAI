from Encoder_X import XClass
from getFromDB import db_race_list_race_data1
import re
import numpy as np

from debug import stream_hdl, file_hdl

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("CourseDistanceClass"))

class CourseDistanceClass(XClass):

    def get(self):
        raceData1List = db_race_list_race_data1(self.race_id)
        # 距離取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = raceData1List[0].split(":")[0]
        # 芝右1600m
        # 数字以外を削除
        sep1 = re.sub(r'\D', '', sep1)
        sep1 = sep1.replace(" ", "")
        # 他と統一するためリストにする
        self.xList = [float(sep1)]
        
    def pad(self):
        pass

    def nrm(self):
        # 最長距離で割って標準化
        MAX_DISTANCE = 3600.0
        npcdList = np.array(self.xList)
        if np.max(npcdList / MAX_DISTANCE) > 1:
            # TODO: [WARNING] npcdList = [23600.], race_id = 2013060501116
            logger.warning("npcdList = {0}, race_id = {1}".format(npcdList, self.race_id))
        npcdList = npcdList / MAX_DISTANCE
        self.xList = npcdList.tolist()
