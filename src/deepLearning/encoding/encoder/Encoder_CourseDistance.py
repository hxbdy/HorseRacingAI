from Encoder_X import XClass
from getFromDB import db_race_list_race_data1
import re
import numpy as np

import logging
logger = logging.getLogger("CourseDistanceClass")

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

    def fix(self):
        XClass.fix(self)

    def pad(self):
        XClass.pad(self)

    def nrm(self):
        # 最長距離で割って標準化
        MAX_DISTANCE = 3600.0
        npcdList = np.array(self.xList)
        npcdList = npcdList / MAX_DISTANCE
        self.xList = npcdList.tolist()
