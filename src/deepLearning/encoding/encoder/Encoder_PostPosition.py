import Encoder_X
from getFromDB import db_race_list_post_position
import numpy as np

import logging
logger = logging.getLogger(__name__)

class PostPositionClass(Encoder_X):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        postPositionList = db_race_list_post_position(self.race_id)
        self.xList = postPositionList

    def fix(self):
        Encoder_X.fix(self)

    def pad(self):
        # 枠番リスト拡張
        adj_size = abs(Encoder_X.pad_size - len(self.xList))

        if len(self.xList) < Encoder_X.pad_size:
            # 要素を増やす
            # ダミーデータ：拡張サイズに達するまで，1から順に追加．
            for i in range(adj_size):
                self.xList.append(i%8+1)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        # 枠番標準化
        # sigmoidで標準化
        nPostPositionList = np.array(self.xList)
        nPostPositionList = 1/(1+np.exp(nPostPositionList))
        self.xList = nPostPositionList.tolist()

    def adj(self):
        self.xList = Encoder_X.adj(self)
        return self.xList
