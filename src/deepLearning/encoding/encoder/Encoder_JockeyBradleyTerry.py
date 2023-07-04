from Encoder_BradleyTerry import BradleyTerryClass

class JockeyBradleyTerryClass(BradleyTerryClass):

    def get(self):
        self.xList = self.nf.db_race_list_jockey(self.race_id)
        self.col_num = len(self.xList)

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
