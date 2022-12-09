from Encoder_BradleyTerry import BradleyTerryClass
from getFromDB import db_race_list_horse_id, db_horse_father

from debug import stream_hdl, file_hdl

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("ParentBradleyTerryClass"))

class ParentBradleyTerryClass(BradleyTerryClass):
    def get(self):
        childList = db_race_list_horse_id(self.race_id)
        parentList = []
        for i in range(len(childList)):
            # 父のidを取得
            parent = db_horse_father(childList[i])
            parentList.append(parent)
        self.xList = parentList
        self.col_num = len(self.xList)
