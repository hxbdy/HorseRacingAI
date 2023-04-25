from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import numpy as np

from Encoder_X import XClass

class RankOneHotClass(XClass):

    def get(self):
        # 馬番で昇順ソートされた順位を文字列で取得
        self.xList = self.nf.db_race_list_rank(self.race_id)

    def fix(self):
        retList = []
        # 順位を int 変換する
        # 着順"取"のような数字以外は99位とする
        # ex: https://db.netkeiba.com/race/198608010111/
        for i in range(len(self.xList)):
            if self.xList[i].isdigit():
                retList.append(int(self.xList[i]))
            else:
                retList.append(99)
        self.xList = retList

    def pad(self):
        # リスト拡張
        # ダミーデータ：99を追加．
        super().pad(99)

    def nrm(self):
        '''1位を1としたone-hotラベルを作成'''
        sorted_x = sorted(self.xList)
        min_x = sorted_x[0]
        self.xList = np.where(np.array(self.xList) == min_x, 1, 0)
