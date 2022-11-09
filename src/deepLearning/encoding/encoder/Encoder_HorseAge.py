import numpy as np
from dateutil.relativedelta import relativedelta

import Encoder_X
from getFromDB import db_race_list_horse_id, db_horse_bod, db_race_date

import logging
logger = logging.getLogger(__name__)

class HorseAgeClass(Encoder_X):
    def __init__(self):
        super().__init__()
        self.d0 = 0
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        if self.race_id == '0':
            logger.critical("ERROR : SET race_id")
        else:
            # 出走馬の誕生日リストを作成
            horseList = db_race_list_horse_id(self.race_id)
            bdList = []
            for horse_id in horseList:
                bod = db_horse_bod(horse_id)
                bdList.append(bod)
            self.xList = bdList
            # レース開催日を取得
            self.d0 = db_race_date(self.race_id)

    def fix(self):
        if self.d0 == 0:
            logger.critical("ERROR : SET d0")
        # 標準化の前に誕生日を日数表記にしておく
        bdList = self.xList
        for i in range(len(bdList)):
            dy = relativedelta(self.d0, bdList[i])
            age = dy.years + (dy.months / 12.0) + (dy.days / 365.0)
            bdList[i] = age
        self.xList = bdList

    def pad(self):
        # 年齢リスト拡張
        adj_size = abs(Encoder_X.pad_size - len(self.xList))

        if len(self.xList) < Encoder_X.pad_size:
            # 要素を増やす
            # ダミーデータ：平均値
            mean_age = np.mean(self.xList)
            for i in range(adj_size):
                self.xList.append(mean_age)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        # 馬年齢標準化
        # 若いほうが強いのか, 年季があるほうが強いのか...
        # 最高値ですべてを割る
        nHorseAgeList = np.array(self.xList)
        maxAge = np.max(nHorseAgeList)
        nHorseAgeList = nHorseAgeList / maxAge
        self.xList = nHorseAgeList.tolist()

    def adj(self):
        self.xList = Encoder_X.adj(self)
        return self.xList
