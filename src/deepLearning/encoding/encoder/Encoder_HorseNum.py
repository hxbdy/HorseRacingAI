from Encoder_X import XClass
from getFromDB import db_race_num_horse

import logging
logger = logging.getLogger(__name__)

class HorseNumClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        self.xList = db_race_num_horse(self.race_id)
        
    def fix(self):
        XClass.fix(self)

    def pad(self):
        XClass.pad(self)

    def nrm(self):
        # 最大出走馬数で割って標準化
        self.xList = [float(self.xList[0]) / XClass.pad_size]

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList
