from Encoder_X import XClass
from getFromDB import db_race_num_horse

import logging
logger = logging.getLogger("HorseNumClass")

class HorseNumClass(XClass):

    def get(self):
        self.xList = db_race_num_horse(self.race_id)

    def nrm(self):
        # 最大出走馬数で割って標準化
        self.xList = [float(self.xList[0]) / XClass.pad_size]
