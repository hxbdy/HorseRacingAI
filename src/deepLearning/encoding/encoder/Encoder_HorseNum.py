import Encoder_X
from getFromDB import db_race_num_horse

import logging
logger = logging.getLogger(__name__)

class HorseNumClass(Encoder_X):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        self.xList = db_race_num_horse(self.race_id)
        
    def fix(self):
        Encoder_X.fix(self)

    def pad(self):
        Encoder_X.pad(self)

    def nrm(self):
        # 最大出走馬数で割って標準化
        self.xList = [float(self.xList[0]) / Encoder_X.pad_size]

    def adj(self):
        self.xList = Encoder_X.adj(self)
        return self.xList
