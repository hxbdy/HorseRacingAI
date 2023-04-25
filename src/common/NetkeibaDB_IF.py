# DB に問い合わせ、取得したデータを整形する
# どこでデータ整形しているのかがわからなくなるため
# ここで行って良い変換処理はDBから取得したデータの変換のみ
# エンコードに都合の良いように変換する作業は各クラスのget, fixで行う

import re
from datetime import date
from typing   import OrderedDict

from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from NetkeibaDB    import NetkeibaDB
from file_path_mgr import path_ini

class NetkeibaDB_IF:
    def __init__(self, loc, read_only=False) -> None:
        """NetkeibaDBにアクセスするためのインタフェース
        loc: DBの展開場所の指定.書き込みを行う場合はROM, 読み取りのみならRAMを指定する
        """
        # load DB
        path_netkeibaDB = path_ini('common', 'path_netkeibaDB')
        self.netkeibaDB = NetkeibaDB(path_netkeibaDB, loc, read_only)

    def db_race_1st_odds(self, race_id):
        # 指定レースの1位オッズをfloatで返す
        odds = self.netkeibaDB.sql_mul_tbl("race_info", ["odds"], ["race_id", "result"], [race_id, "1"], False)
        return float(odds[0])

    def db_race_list_id(self, start_year = 0, end_year = 9999, limit = -1, pattern = False):
        """yearを含む年のレースまでをlimit件取得する
        limit を指定しない場合は全件検索
        pattern : True 重賞レースのみを取得する, False 全レースを取得する
        """

        # DB上のrace_idの上4桁は開催年前提
        if len(str(start_year)) != 4:
            logger.critical("len(str(start_year)) != 4")
            start_year = "0000"
        if len(str(end_year)) != 4:
            logger.critical("len(str(end_year)) != 4")
            end_year = "9999"
        start_year = str(start_year) + "00000000"
        end_year   = str(end_year)   + "99999999"

        if limit <= 0:
            # 全件検索
            # SQLite Int の最大値 2**63 -1
            limit = 9223372036854775807

        totalRaceList = self.netkeibaDB.sql_mul_distinctColCnt(start_year, end_year, limit, pattern)

        return totalRaceList

    def db_race_date(self, race_id):
        """レース開催日をdate型で返す
        race_info テーブルの date から検索する"""

        raceDate = self.netkeibaDB.sql_mul_tbl("race_info", ["date"], ["race_id"], [race_id], False)
        raceDate = raceDate[0]

        year, month, day = raceDate.split('/')
        return date(int(year), int(month), int(day))

    def db_race_grade(self, race_id):
        # レースのグレードを返す
        # 不明の場合-1を返す
        raceGrade = self.netkeibaDB.sql_mul_tbl("race_info", ["grade"], ["race_id"], [race_id], False)
        return int(raceGrade[0])
    
    def db_race_time(self, race_id, horse_id):
        """ race_info テーブルから走破タイム[sec]を返す """
        race_time = self.netkeibaDB.sql_one_race_info(race_id, horse_id, "time")

        if (race_time is None) or (race_time == "") or (race_time == "None"):
            sec = float(0)
        else:
            t = re.findall("\d+", race_time)
            # ex) 1:18.7 -> [1, 18, 7] -> 78.7 [sec]
            if len(t) == 3:
                min, sec, msec = t
                sec = 60 * float(min) + float(sec) + 0.1 * float(msec)
            else:
                sec = float(0)

        return sec

    def db_race_list_prize(self, race_id):
        # レースの賞金をリストで返す
        # (降順ソートされているか未確認)
        prizeList = self.netkeibaDB.sql_mul_tbl("race_result", ["prize"], ["race_id"], [race_id], False)
        for i in range(len(prizeList)):
            prizeList[i] = str(prizeList[i])
        return prizeList

    def db_race_num_horse(self, race_id):
        # 出走する頭数を返す
        return self.netkeibaDB.sql_one_rowCnt("race_result", "race_id", race_id)

    def db_race_list_race_data1(self, race_id):
        # race_result テーブルの race_data1 列のデータを取得する
        return self.netkeibaDB.sql_mul_tbl("race_result", ["race_data1"], ["race_id"], [race_id], False)

    def db_race_list_horse_id(self, race_id):
        # 馬番でソートされた出走する馬のIDリストを返す
        return self.netkeibaDB.sql_mul_sortHorseNum(["race_info.horse_id"], "race_info.race_id", race_id)

    def db_horse_bod(self, horse_id):
        # 馬の誕生日を返す
        data = self.netkeibaDB.sql_one_horse_prof(horse_id, "bod")
        birthYear = int(data.split("年")[0])
        birthMon = int(data.split("年")[1].split("月")[0])
        birthDay = int(data.split("月")[1].split("日")[0])
        return date(birthYear, birthMon, birthDay)

    def db_race_list_burden_weight(self, race_id):
        # 斤量リストをfloatに変換して返す
        burdenWeightList = self.netkeibaDB.sql_mul_sortHorseNum(["race_info.burden_weight"], "race_info.race_id", race_id)
        for i in range(len(burdenWeightList)):
            burdenWeightList[i] = float(burdenWeightList[i])
        return burdenWeightList

    def db_race_list_post_position(self, race_id):
        # 枠番リストをfloatに変換して返す
        postPositionList = self.netkeibaDB.sql_mul_sortHorseNum(["race_info.post_position"], "race_info.race_id", race_id)
        for i in range(len(postPositionList)):
            postPositionList[i] = float(postPositionList[i])
        return postPositionList

    def db_race_list_jockey(self, race_id):
        # 騎手リストを返す
        jockeyIDList = self.netkeibaDB.sql_mul_sortHorseNum(["race_info.jockey_id"], "race_info.race_id", race_id)
        for i in range(len(jockeyIDList)):
            jockeyIDList[i] = str(jockeyIDList[i])
        return jockeyIDList

    def db_race_cnt_jockey(self, jockey_id, lower_year, upper_year):
        # jockey_infoテーブルから騎手の lower_year から upper_year までの総出場回数を求める
        return self.netkeibaDB.sql_one_jockey_total(jockey_id, str(lower_year), str(upper_year))
    
    def db_race_info_jockey_list(self, lower, upper):
        # race_infoテーブルから(year)年に騎乗した騎手のリスト
        jockey_list = self.netkeibaDB.sql_mul_jockey_cnt(lower, upper)
        return jockey_list
    
    def db_race_info_jockey_cnt(self, jockey_id, lower, upper):
        cnt = self.netkeibaDB.sql_one_rowCnt_range("race_info", "jockey_id", jockey_id, lower, upper)
        return cnt

    def db_horse_list_parent(self, horse_id):
        # 親馬のIDリストを返す
        parent_list = self.netkeibaDB.sql_mul_tbl("horse_prof", ["blood_f", "blood_ff", "blood_fm", "blood_m", "blood_mf", "blood_mm"], ["horse_id"], [horse_id], False)
        parent_list = parent_list[0]
        return parent_list

    def db_horse_list_perform(self, horse_id):
        # パフォーマンス計算に必要な列を返す
        col = ["horse_id", "venue", "time", "burden_weight", "course_condition", "distance", "grade"]
        race = self.netkeibaDB.sql_mul_tbl("race_info", col, ["horse_id"], [horse_id], False)
        return race

    def db_race_list_margin(self, race_id):
        """順位でソートされた{馬番:着差}形式の辞書を返す"""

        # 着差を文字列のリストで返す(着順)
        marginList = self.netkeibaDB.sql_mul_tbl("race_result", ["margin"], ["race_id"], [race_id], False)
        for i in range(len(marginList)):
            marginList[i] = str(marginList[i])
        
        # 順位でソートされた馬番を取得
        horse_number_list = self.netkeibaDB.sql_mul_sortRank(["race_info.horse_number"], "race_info.race_id", race_id)

        margin_dict = OrderedDict(zip(horse_number_list, marginList))
        return margin_dict

    def db_race_rank(self, race_id, horse_id):
        # race_id で horse_id は何位だったか取得
        return self.netkeibaDB.sql_one_race_info(race_id, horse_id, "result")

    def db_race_list_1v1(self, horse_id_1, horse_id_2):
        # horse_id_1, horse_id_2 が出走したレースリストを返す
        return self.netkeibaDB.sql_mul_race_id_1v1(horse_id_1, horse_id_2)
    
    def db_horse_parent(self, horse_id, parent):
        """親のhorse_idを返す
        horse_id
        parent: f,ff,fm,m,mf,mm
        """
        blood = "blood_" + parent
        return self.netkeibaDB.sql_one_horse_prof(horse_id, blood)

    def db_race_list_rank(self, race_id):
        # 馬番で昇順ソートされた順位を文字列で返す
        rankList = self.netkeibaDB.sql_mul_sortHorseNum(["race_info.result"], "race_info.race_id", race_id)
        for i in range(len(rankList)):
            rankList[i] = str(rankList[i])
        return rankList

    def db_race_last_3f(self, race_id, horse_id):
        # 上がり3ハロンを返す
        last_3f = self.netkeibaDB.sql_one_race_info(race_id, horse_id, "last_3f")
        return last_3f

    def db_race_last_race(self, race_id, horse_id, pattern):
        # horse_id が出走したレースのうち、race_idの直前に走ったレースIDを返す
        # 見つからなかった場合、出走レース一覧から一番最近のrace_idを返す
        # 指定のrace_idより古いレースがない場合は指定のrace_idをそのまま返す

        # これは直前の調子をはかるために使う
        # 直前のレースが重賞以外のとき、現状は重賞まで遡ってタイムを取得している。
        # が、直前のレースのグレードは関係ないと思う。ラスト3ハロンタイムは

        # horse_idの出走レース一覧をrace_infoテーブルから取得する
        race_list = self.netkeibaDB.sql_mul_tbl("race_info", ["race_id"], ["horse_id"], [horse_id], pattern)

        # 昇順ソート
        # race_id から開催日YYYYMMDD  が取得できるとは限らないため、
        # race_resultテーブルのrace_data2列にある開催日を使ってソートする
        race_list = self.db_race_list_sort(race_list)
        if len(race_list) == 0:
            # 見つからなかった場合、空のリストをそのまま返す
            return race_list

        # 直前の重賞レースIDを返す
        # TODO: 地方競馬の場合、ラスト3fが記録されていない場合がある。それの回避策
        if race_id in race_list:
            last_race_id = race_list.index(race_id) - 1
            if(last_race_id < 0):
                # race_id が一番古い重賞レースだった
                # race_id をそのまま返す
                return race_id
            else:
                # race_id の直前の race_id が見つかった
                return race_list[last_race_id]
        else:
            # predict 時にはここを通過する (DBには無いレースを走るため)
            # race_id がなかった場合、最新のrace_idを返す
            return race_list[-1]

    def db_race_list_sort(self, race_id_list):
        # race_id_list を開催日の昇順でソートする
        # 開催日は race_info テーブルの date を参照する

        # {race_id : 開催日} 辞書を作成
        race_date_dict = OrderedDict()
        for race_id in race_id_list:
            col_date = self.netkeibaDB.sql_mul_tbl("race_info", ["date"], ["race_id"], [race_id], False)
            # 複数取れるけど1つで良い
            col_date = col_date[0]
            # ex : "2023/03/05"
            num_list = re.findall('\d{4}|\d{2}', col_date)
            dt = date(int(num_list[0]), int(num_list[1]), int(num_list[2]))
            race_date_dict.update({race_id : dt})

        # アイテム(日付)でソート
        race_id_list_sorted = sorted(race_date_dict.items(), key=lambda x: x[1])

        # race_idのみ取り出す
        # ex : [('202207010311', datetime.date(2022, 1, 9)), ('202206030511', datetime.date(2022, 4, 9)),  ... ]
        race_id_list_sorted = list(map(lambda x: x[0], race_id_list_sorted))

        return race_id_list_sorted

    def db_horse_weight(self, race_id, horse_id):
        '''race_resultテーブルから馬体重を取得する'''
        return self.netkeibaDB.sql_one_race_result(race_id, horse_id, "horse_weight")

    def db_corner_pos(self, race_id, horse_id):
        '''コーナー通過時点での順位を返す
        return: コーナー通過時点での順位をlist(int, int, ...)返す
        '''
        corner_pos = self.netkeibaDB.sql_one_race_info(race_id, horse_id, "corner_pos")

        # 取得できなかった場合Noneを返す
        if type(corner_pos) != str:
            return None

        # 空文字ならNoneを返す
        if " " in corner_pos:
            return None

        corner_pos_list = corner_pos.split("-")
        corner_pos_list = list(map(int, corner_pos_list))

        return corner_pos_list

    def db_pace(self, race_id, horse_id):
        """レースのペースを取得する
        馬ごとのペースではないので注意
        return: [first3f, last3f]
        """
        pace = self.netkeibaDB.sql_one_race_info(race_id, horse_id, "pace")

        # 取得できなかった場合Noneを返す
        if type(pace) != str:
            return None

        pace_list = pace.split("-")

        if len(pace_list) != 2:
            pace_list = [float(0), float(0)]

        pace_list = list(map(float, pace_list))

        return pace_list

    def db_insert_untracked_race_id(self, race_id_list):
        """untracked_race_idテーブルに登録する
        """
        self.netkeibaDB.sql_insert_RowToUntrackedRaceId(race_id_list)

    def db_insert_untracked_horse_id(self, horse_id_list):
        """untracked_horse_idテーブルに登録する
        """
        self.netkeibaDB.sql_insert_RowToUntrackedHorseId(horse_id_list)

    def db_pop_untracked_race_id(self):
        """untracked_race_idテーブルすべてpopする
        """
        race_id_list = self.netkeibaDB.sql_mul_all("untracked_race_id")
        # [('198608010111',), ('198606010111',), ('198606010109',)...]
        ret = []
        for i in race_id_list:
            ret.append(i[0])
            self.db_del_record_untracked_race_id(i[0])
        return ret

    def db_pop_untracked_horse_id(self):
        """untracked_horse_idテーブルすべてpopする
        """
        horse_id_list = self.netkeibaDB.sql_mul_all("untracked_horse_id")
        ret = []
        for i in horse_id_list:
            ret.append(i[0])
            self.db_del_record_untracked_horse_id(i[0])
        return ret

    def db_insert_race_result(self, target_col, data_list):
        horse_id_idx = target_col.index("horse_id")
        race_id_idx  = target_col.index("race_id")
        for data in data_list:
            duplicate = self.netkeibaDB.sql_one_race_result(data[race_id_idx], data[horse_id_idx], "race_id")
            if duplicate is None:
                self.netkeibaDB.sql_insert_Row("race_result", target_col, [data])
            else:
                logger.info("race_id = {0} had scraped".format(data[race_id_idx]))

    def db_filter_scrape_race_id(self, race_id_list):
        # race_resultテーブルにあるならスクレイプ済み
        checked_list = []
        for i in range(len(race_id_list)):
            if self.netkeibaDB.sql_isIn("race_result", ["race_id='{0}'".format(race_id_list[i])]) == False:
                checked_list.append(race_id_list[i])
        return checked_list

    def db_del_record_untracked_race_id(self, race_id):
        """untracked_race_id テーブルから指定レコードを削除する"""
        self.netkeibaDB.sql_del_row("untracked_race_id", ["race_id"], [race_id])

    def db_del_record_untracked_horse_id(self, horse_id):
        """untracked_horse_id テーブルから指定レコードを削除する"""
        self.netkeibaDB.sql_del_row("untracked_horse_id", ["horse_id"], [horse_id])

    def db_not_retired_list(self, horse_id_list):
        """ 引退馬としてテーブルに登録されていないhorse_idのみを返す
        注意) JRAへの登録から判定しているため、外国の馬は現状飛ばせない。例: モンジュー
        """
        checked_list = []
        for horse_id in horse_id_list:
            if self.netkeibaDB.sql_isIn("horse_prof",["horse_id='{}'".format(horse_id),"retired_flg='1'"]) == False:
                checked_list.append(horse_id)
        return checked_list

    def db_upsert_horse_prof(self, prof_contents, blood_list, horseID, horse_title, check, retired, app_list, target_col_hp):
        ## テーブルへの保存
        #- horse_profテーブル
        data_list = [[*prof_contents, *blood_list, horseID, horse_title, check, retired, *app_list]] #★順序対応確認
        # 存在確認して，あればUPDATE，なければINSERT
        if len(self.netkeibaDB.sql_mul_tbl("horse_prof",["*"],["horse_id"],[horseID], False)) > 0:
            self.netkeibaDB.sql_update_Row("horse_prof", target_col_hp, data_list, ["horse_id = '{}'".format(horseID)])
        else:
            self.netkeibaDB.sql_insert_Row("horse_prof", target_col_hp, data_list)
        logger.debug("save horse data on horse_prof table, horse_id={}".format(horseID))

    def db_diff_insert_race_info(self, perform_contents, target_col_ri, horseID):
        #- race_infoテーブル
        # 既にdbに登録されている出走データ数と，スクレイプした出走データ数を比較して，差分を追加
        dif = len(perform_contents) - len(self.netkeibaDB.sql_mul_tbl("race_info",["*"],["horse_id"],[horseID], False))
        logger.debug("dif = {}".format(dif))
        if dif > 0:
            data_list = perform_contents[:dif]
            self.netkeibaDB.sql_insert_Row("race_info", target_col_ri, data_list)
        else:
            pass
        logger.debug("save horse data on race_info table, horse_id={}".format(horseID))

    def db_insert_pandas(self, table, table_name):
        self.netkeibaDB.sql_upsert(table, table_name)

    def interface_make_index(self):
        # インデックスを貼る
        # 現状、1度しか呼ばない。断片化を考慮していない。
        logger.info("indexing")
        self.netkeibaDB.make_index()

    def db_horse_review(self, horse_id):
        """レビュー値をfloatで返す。Noneはデフォルト値で埋める"""
        review = list(self.netkeibaDB.sql_one_review(horse_id))
        # print("review = ", review)
        # レビューグラフの中央のピクセル数値
        pad_50 = (26.0, 58.0, 58.0, 26.0)

        for i in range(len(review)):
            if review[i] is None:
                review[i] = float(pad_50[i % 4])
            else:
                review[i] = float(review[i])
        return review
