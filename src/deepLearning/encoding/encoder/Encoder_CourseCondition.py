import logging

from Encoder_X import XClass
from debug     import stream_hdl, file_hdl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("CourseConditionClass"))
class CourseConditionClass(XClass):

    def get(self):
        raceData1List = self.nf.db_race_list_race_data1(self.race_id)
        # コース状態取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = raceData1List[0].split(":")[2]
        #  良 / 発走 
        sep1 = sep1.split("/")[0]
        # 良
        sep1 = sep1.replace(" ", "")

        self.xList = sep1

    def fix(self):
        ALGO = 2

        if ALGO == 1:
            # 馬場状態のone-hot表現(ただし良は全て0として表現する)
            condition_dict = {'良':-1, '稍':0, '稍重':1, '重':2, '不良':3, '良ダート':4, '稍重ダート':5, '重ダート':6, '不良ダート':7}
            condition_onehot = [0] * len(condition_dict)
            hot_idx = condition_dict[self.xList]
            if hot_idx != -1:
                condition_onehot[hot_idx] = 1
            self.xList = condition_onehot
        elif ALGO == 2:
            # 馬場状態のone-hot表現
            condition_dict = {'良':0, '稍':1, '稍重':2, '重':3, '不良':4, '良ダート':5, '稍重ダート':6, '重ダート':7, '不良ダート':8}
            condition_onehot = [0] * len(condition_dict)
            hot_idx = condition_dict[self.xList]
            condition_onehot[hot_idx] = 1
            self.xList = condition_onehot

    def pad(self):
        pass
