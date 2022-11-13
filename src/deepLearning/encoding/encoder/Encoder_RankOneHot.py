from Encoder_X import XClass
from getFromDB import db_race_list_rank

import logging
logger = logging.getLogger("RankOneHotClass")

class RankOneHotClass(XClass):

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
        # ダミーデータ：99を追加．
        super().pad(99)

    def nrm(self):
        # 最小値の順位を取得
        rank_min = min(self.xList)

        if rank_min != 1:
            # pad処理により1位の馬がリストから無くなってしまった。
            # 残っている馬の中で一番順位がよかった馬を正解とする
            logger.info("Fastest rank : 1 -> {0} | https://db.netkeiba.com/race/{1}/".format(rank_min, self.race_id))

        # 最高順位を1とする
        for i in range(len(self.xList)):
            if self.xList[i] == rank_min:
                self.xList[i] = 1
            else:
                self.xList[i] = 0
