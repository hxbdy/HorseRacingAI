import re
import numpy as np

from Encoder_X import XClass

class CourseDistanceClass(XClass):

    def get(self):
        raceData1List = self.nf.db_race_list_race_data1(self.race_id)
        # 距離取得
        # 3桁以上4桁以下の数値のみ取り出す。
        # 例えば、https://race.netkeiba.com/race/result.html?race_id=201306050111 では
        # '芝右 内2周3600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:25'
        # のように、距離よりも前に別情報の数値があるケースに対応する。
        num_list = re.findall('\d{3,4}', raceData1List[0])
        num = float(num_list[0])
        # 他と統一するためリストにする
        self.xList = [num]
        
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
