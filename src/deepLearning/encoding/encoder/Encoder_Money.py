from Encoder_X import XClass
from getFromDB import db_race_list_prize

import logging
logger = logging.getLogger("MoneyClass")

class MoneyClass(XClass):

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

    def nrm(self):
        # 賞金標準化
        # 1位賞金で割る
        # moneyList は float前提
        money1st = self.xList[0]
        moneyNrmList = []
        for m in self.xList:
            moneyNrmList.append(m / money1st)
        self.xList = moneyNrmList
