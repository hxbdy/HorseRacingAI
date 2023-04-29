import re
import numpy as np

from Encoder_X import XClass

class CourseDistanceClass(XClass):

    def get(self):
        distance = self.nf.db_race_distance(self.race_id)
        # 他と統一するためリストにする
        self.xList = [distance]
        
    def pad(self):
        # paddingしない
        # 関数ごと削除するとXClassのpad()が実行されるのでpassしておく
        pass

    def nrm(self):
        # 最長距離で割って標準化
        MIN_DISTANCE =  800.0
        MAX_DISTANCE = 3600.0
        npcdList = np.array(self.xList)
        if ((npcdList > MAX_DISTANCE) or (npcdList < MIN_DISTANCE)):
            # データ取得に失敗している可能性
            self.logger.warning("npcdList = {0}, race_id = {1}".format(npcdList, self.race_id))
        npcdList = npcdList / MAX_DISTANCE
        self.xList = npcdList.tolist()
