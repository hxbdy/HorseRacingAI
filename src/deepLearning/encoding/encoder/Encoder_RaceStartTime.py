

from Encoder_X import XClass

class RaceStartTimeClass(XClass):

    def get(self):
        raceData1List = self.nf.db_race_list_race_data1(self.race_id)
        # 出走時刻取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = raceData1List[0].split("/")[3]
        #  発走 : 15:35
        sep1 = sep1.split(" : ")[1]
        #  15:35
        sep1 = sep1.replace(" ", "")

        self.xList = sep1

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
        