from Encoder_X import XClass
from getFromDB import db_race_list_prize

import logging
logger = logging.getLogger(__name__)

class MoneyClass(XClass):
    def __init__(self):
        super().__init__()

    def set(self, race_id):
        super().set(race_id)

    def get(self):
        self.xList = db_race_list_prize(self.race_id)
    
    def fix(self):
        # 賞金リストをfloat変換する
        rowList = self.xList
        moneyList = []
        for m in rowList:
            if m == "":
                fm = "0.0"
            else:
                fm = m.replace(",","")
            moneyList.append(float(fm))
        self.xList = moneyList

    def pad(self):
        adj_size = abs(XClass.pad_size - len(self.xList))

        # ダミーデータ：0
        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            for i in range(adj_size):
                self.xList.append(0)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]
