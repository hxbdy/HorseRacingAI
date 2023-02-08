import logging

from Encoder_X import XClass
from debug     import stream_hdl, file_hdl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("HorseNumClass"))

class HorseNumClass(XClass):

    def get(self):
        self.xList = self.nf.db_race_num_horse(self.race_id)

    def nrm(self):
        # 最大出走馬数で割って標準化
        self.xList = [float(self.xList) / XClass.pad_size]

    def pad(self):
        pass
