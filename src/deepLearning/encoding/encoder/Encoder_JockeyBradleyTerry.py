from Encoder_BradleyTerry import BradleyTerryClass

class JockeyBradleyTerryClass(BradleyTerryClass):

    def get(self):
        self.xList = self.nf.db_race_list_jockey(self.race_id)
        self.col_num = len(self.xList)

    def getRankFromDB(self, race_id, jockey_x, jockey_y):
        # race_id で jockey_x と jockey_y は何位だったか取得

        # ((jockey_id, result), ...)
        vals = self.nf.db_race_rank_jockey(race_id)

        rank_x = 0
        rank_y = 0
        for val in vals:
            # logger.debug(f"val = {val}")
            jockey_id, result = val

            if str(result).isdigit():
                result = int(result)
            else:
                # '除'などが稀に入っているため、そのときはビリ扱いとする
                result = self.col_num

            if jockey_id == jockey_x:
                rank_x = result
            if jockey_id == jockey_y:
                rank_y = result

            if (rank_x != 0) and (rank_y != 0):
                break
        
        return rank_x, rank_y

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
                    rank_x, rank_y = self.getRankFromDB(race, horse_x, horse_y)
                    # 勝敗
                    if rank_y < rank_x:
                        win += 1
                    else:
                        lose += 1
                self.wl_table[y][x] = win
                self.wl_table[x][y] = lose
