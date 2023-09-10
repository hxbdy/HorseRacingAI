from Encoder_BradleyTerry import BradleyTerryClass

class JockeyBradleyTerryClass(BradleyTerryClass):
    # self.race_id までの「全騎手リスト」と 「今回出場する騎手リスト」を取得
    # 全騎手リストでパワーを計算、その中から今回の騎手を取り出す

    def get(self):
        # 「全騎手リスト」を取得
        self.xList = self.nf.db_race_info_jockey_list('0', self.race_id)
        self.col_num = len(self.xList)

        self.logger.debug("col_num = {0}".format(self.col_num))

        # 「今回出場する騎手リスト」を取得
        self.target = self.nf.db_race_list_jockey(self.race_id)

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

                # TODO: 騎手vs騎手の勝敗ではなく、単純なこのレースまでの勝利数比較のほうが良い判断材料にならないか？
                races = self.nf.db_race_list_jockey_1v1(horse_y, horse_x, self.race_id)

                self.logger.debug("{0} vs {1} history ~ {2} | race_id_list = {3}".format(horse_y, horse_x, self.race_id, races))
                for race in races:
                    # race で horse_x, y は何位だったか取得
                    rank_x, rank_y = race

                    if str(rank_x).isdigit():
                        rank_x = int(rank_x)
                    else:
                        # '除'などが稀に入っているため、そのときはビリ扱いとする
                        rank_x = self.col_num

                    if str(rank_y).isdigit():
                        rank_y = int(rank_y)
                    else:
                        # '除'などが稀に入っているため、そのときはビリ扱いとする
                        rank_y = self.col_num

                    # 勝敗
                    if rank_y < rank_x:
                        win += 1
                    else:
                        lose += 1
                self.wl_table[y][x] = win
                self.wl_table[x][y] = lose

    def fix(self):
        self.calcPower()

        a = []
        for jockey_id in self.target:

            try:
                idx = self.xList.index(jockey_id)
                val = self.p[idx]
            except ValueError:
                # 以前に出場経験がない場合はこちら
                # 平均のパワーとする
                val = sum(self.p) / len(self.p)

            a.append(val)

        self.logger.debug("power = {0}".format(a))
        self.xList = a
