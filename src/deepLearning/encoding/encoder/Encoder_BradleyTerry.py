from Encoder_X import XClass

from getFromDB import db_race_list_horse_id, db_race_rank, db_race_list_1v1

import logging
logger = logging.getLogger("BradleyTerryClass")

class BradleyTerryClass(XClass):

    def get(self):
        self.xList = db_race_list_horse_id(self.race_id)
        self.col_num = len(self.xList)

    def getRankFromDB(self, race_id, horse_id):
        # race_id で horse_id は何位だったか取得
        val = db_race_rank(race_id, horse_id)
        if val.isdigit():
            rank = int(val)
        else:
            # '除'などが稀に入っているため、そのときはビリ扱いとする
            rank = self.col_num
        return rank

    def gen_wl_table(self):
        # 馬数x馬数の対戦表作成
        self.wl_table = [[-1 for j in range(self.col_num)] for i in range(self.col_num)]

        for y in range(self.col_num):
            horse_y = self.xList[y]
            start_x = y + 1
            for x in range(start_x, self.col_num):
                win = 0
                lose = 0
                horse_x = self.xList[x]
                races = db_race_list_1v1(horse_y, horse_x)
                for race in races:
                    # race で horse_x, y は何位だったか取得
                    rank_y = self.getRankFromDB(race, horse_y)
                    rank_x = self.getRankFromDB(race, horse_x)
                    # 勝敗
                    if rank_y < rank_x:
                        win += 1
                    else:
                        lose += 1
                self.wl_table[y][x] = win
                self.wl_table[x][y] = lose        

    def calcPower(self):
        self.gen_wl_table()
        self.p = [1 for i in range(self.col_num)]
        for i in range(20):
            self.calcFrac()
            self.p_div()

    def calcFrac(self):
        for y in range(self.col_num):
            w = 0 # 分子
            b = 0 # 分母
            for x in range(self.col_num):
                if self.wl_table[y][x] != -1:
                    w += self.wl_table[y][x]
                    if (self.p[y] + self.p[x]) == 0:
                        b = 0
                    else:
                        b += float((self.wl_table[y][x] + self.wl_table[x][y]) / (self.p[y] + self.p[x]))
            if(b == 0):
                self.p[y] = 0
            else:
                self.p[y] = float(w / b)

    def p_div(self):
        sum_p = sum(self.p)
        for i in range(self.col_num):
            if sum_p == 0:
                self.p[i] = 0
            else:
                self.p[i] /= sum_p

    def fix(self):
        self.calcPower()
        self.xList = self.p

    def pad(self):
        # リスト拡張
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            # ダミーデータ：0を追加．
            for i in range(adj_size):
                self.xList.append(0)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]
        