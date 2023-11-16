import numpy as np
from Encoder_X import XClass

class TimeClass(XClass):

    def get(self):
        # 出走する馬一覧取得
        horse_id_list = self.nf.db_race_list_horse_id(self.race_id)
        
        # race_info テーブルからその馬の走破タイムを取得
        time_list = []
        for horse_id in horse_id_list:
            time_list.append(self.nf.db_race_time(self.race_id, horse_id))
        
        self.xList = time_list
        self.logger.debug(self.xList)

    def pad(self):
        # 最下位のタイムで埋める
        super().pad(max(self.xList))

    def nrm(self):
        np_xList = np.array(self.xList)
        
        # zscore
        # IdentityWithLoss を使用する場合
        # val = self.zscore(np_xList, axis=-1, reverse=True)
        # self.xList = val.tolist()

        # 合計で割って和が1になるようにする
        # SoftmaxWithLoss を使用するため
        total = np_xList.sum()
        self.logger.debug(f"{np_xList} / {total}")

        nrm_xList = np_xList / total
        self.logger.debug(f"nrm_xList.sum() = {nrm_xList.sum()}")

        self.xList = nrm_xList.tolist()
