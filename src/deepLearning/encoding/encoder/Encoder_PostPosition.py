import logging
import numpy as np

from Encoder_X import XClass
from debug     import stream_hdl, file_hdl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("PostPositionClass"))

class PostPositionClass(XClass):

    def get(self):
        postPositionList = self.nf.db_race_list_post_position(self.race_id)
        self.xList = postPositionList

    def pad(self):
        # 枠番リスト拡張
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
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
        # nPostPositionList = np.array(self.xList)
        # nPostPositionList = 1/(1+np.exp(nPostPositionList))
        # self.xList = nPostPositionList.tolist()

        # zscore
        # 内側有利とする
        nPostPositionList = self.zscore(self.xList, axis=-1, reverse=True)
        self.xList = nPostPositionList.tolist()
