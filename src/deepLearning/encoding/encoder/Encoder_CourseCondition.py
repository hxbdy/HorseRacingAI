from Encoder_X import XClass
from getFromDB import db_race_list_race_data1

import logging
logger = logging.getLogger("CourseConditionClass")

class CourseConditionClass(XClass):

    def get(self):
        raceData1List = db_race_list_race_data1(self.race_id)
        # コース状態取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = raceData1List[0].split(":")[2]
        #  良 / 発走 
        sep1 = sep1.split("/")[0]
        # 良
        sep1 = sep1.replace(" ", "")

        self.xList = sep1

    def fix(self):
        # 馬場状態のone-hot表現(ただし良は全て0として表現する)
        condition_dict = {'良':-1, '稍重':0, '重':1, '不良':2, '良ダート':3, '稍重ダート':4, '重ダート':5, '不良ダート':6}
        condition_onehot = [0] * len(condition_dict)
        hot_idx = condition_dict[self.xList]
        if hot_idx != -1:
            condition_onehot[hot_idx] = 1
        self.xList = condition_onehot

    def pad(self):
        pass
