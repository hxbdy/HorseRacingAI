import Encoder_X
from getFromDB import db_race_list_rank

import logging
logger = logging.getLogger(__name__)

class RankOneHotClass(Encoder_X):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        # 馬番で昇順ソートされた順位を文字列で取得
        self.xList = db_race_list_rank(self.race_id)

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
        adj_size = abs(Encoder_X.pad_size - len(self.xList))

        if len(self.xList) < Encoder_X.pad_size:
            # 要素を増やす
            # ダミーデータ：99を追加．
            for i in range(adj_size):
                self.xList.append(99)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

            # 1位の馬がリストから無くなってしまった。
            # 残ってる馬の中で一番順位がよかった馬を正解とする
            if (1 in self.xList) == False:
                logger.info("1st place horse was deleted, https://db.netkeiba.com/race/{0}/".format(self.race_id))

    def nrm(self):
        # 最小値の順位を取得
        rank_min = min(self.xList)

        # 最高順位を1とする
        for i in range(len(self.xList)):
            if self.xList[i] == rank_min:
                self.xList[i] = 1
            else:
                self.xList[i] = 0

    def adj(self):
        self.xList = Encoder_X.adj(self)
        return self.xList
