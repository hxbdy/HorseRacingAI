from dateutil.relativedelta import relativedelta



from Encoder_X import XClass

class LastRaceLeftClass(XClass):

    def get(self):
        # 出走する馬一覧取得
        horse_id_list = self.nf.db_race_list_horse_id(self.race_id)
        self.xList = horse_id_list
        # 開催日を保持
        # 学習時はDBから日付を設定する
        # 当日はここにその時の日付を設定する
        self.d0 = self.nf.db_race_date(self.race_id)
    
    def fix(self):
        last_race_left_list = []
        for horse_id in self.xList:
            # 前走のrace_id取得
            last_race_id = self.nf.db_race_last_race(self.race_id, horse_id, False)
            if len(last_race_id) == 0:
                last_race_id  = self.race_id
            # 前走の開催日を取得
            last_race_date = self.nf.db_race_date(last_race_id)

            # 経過日数を計算
            delta = relativedelta(self.d0, last_race_date)
            self.logger.debug("horse_id={0}, last_race_id={1}, last_race_date={2}, delta={3}".format(horse_id, last_race_id, last_race_date, delta))

            last_race_left_list.append(delta.years + (delta.months / 12.0) + (delta.days / 365.0))

        self.xList = last_race_left_list

    def nrm(self):
        nx = self.zscore(self.xList, axis=-1, reverse=False)
        self.xList = nx.tolist()
