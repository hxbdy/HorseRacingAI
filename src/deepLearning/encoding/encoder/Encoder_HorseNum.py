from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from Encoder_X import XClass

class HorseNumClass(XClass):

    def get(self):
        self.xList = self.nf.db_race_num_horse(self.race_id)

    def pad(self):
        pass

    def nrm(self):
        # 最大出走馬数で割って標準化
        self.xList = [float(self.xList) / XClass.pad_size]
