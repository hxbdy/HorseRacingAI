import Encoder_BradleyTerry
from getFromDB import db_race_list_horse_id, db_horse_father

import logging
logger = logging.getLogger(__name__)

class ParentBradleyTerryClass(Encoder_BradleyTerry):
    def get(self):
        childList = db_race_list_horse_id(self.race_id)
        parentList = []
        for i in range(len(childList)):
            # 父のidを取得
            parent = db_horse_father(childList[i])
            parentList.append(parent)
        self.xList = parentList
        self.col_num = len(self.xList)
