

from Encoder_X import XClass

class RaceStartTimeClass(XClass):

    def get(self):
        self.xList = self.nf.db_race_start_time(self.race_id)

    def fix(self):
        # 発走時刻の数値化(時*60 + 分)
        t = self.xList.split(":")
        min = float(t[0])*60 + float(t[1])
        self.xList = [min]

    def pad(self):
        pass

    def nrm(self):
        # 遅い時間ほど馬場が荒れていることを表現する
        # 最終出走時間 16:30 = 16 * 60 + 30 = 990 で割る
        self.xList = [self.xList[0] / 990]
        