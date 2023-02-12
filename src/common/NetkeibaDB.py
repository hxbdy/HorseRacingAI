# Netkeiba.py
# DBにアクセスするためSQL発行して結果を加工して返す

# 関数命名ルール
# sql_{A}_{B}()
# {A} = one | mul
# one : 取得する行数が必ず1つ
# mul : 取得する行数が1つ以上
# {B} = 関数名

import logging
import copy
import os

import sqlite3

from debug import stream_hdl, file_hdl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("db"))

class NetkeibaDB:
    def __init__(self, path_db, loc):
        if not os.path.isfile(path_db):
            self.create_table(path_db)

        self.conn = sqlite3.connect(path_db)
        # sqliteを操作するカーソルオブジェクトを作成
        self.cur = self.conn.cursor()
        if loc == "RAM":
            logger.info("DB will be located in RAM")
            self._switch_RAM()
        else:
            logger.info("DB will be located in ROM")
        logger.info("Database {0} loading complete".format(path_db))

    def create_table(self, dbname):
        """データベースの作成
        データベースを新規作成するときに実行する。
        untracked_idテーブル: スクレイピング対象のrace_idを一時的に保持しておく用
        horse_profテーブル: 馬のページにある馬名などの情報と、生年月日などの表・血統の表の情報
        race_infoテーブル: 馬のページにある出走レース情報
        race_resultテーブル: レースのページにあるレース名やレース結果の情報(オッズは含まず)
        jockey_infoテーブル: 騎手の騎乗回数を1年ごとに計上してまとめたテーブル
        """
        os.makedirs(os.path.dirname(dbname))

        conn = sqlite3.connect(dbname)
        cur = conn.cursor()
        cur.execute('CREATE TABLE untracked_race_id(race_id TEXT, PRIMARY KEY(race_id))')
        cur.execute('CREATE TABLE untracked_horse_id(horse_id TEXT, PRIMARY KEY(horse_id))')
        cur.execute('CREATE TABLE horse_prof(horse_id PRIMARY KEY, bod, trainer, owner, owner_info, producer, area, auction_price, earned, lifetime_record, main_winner, relative, blood_f, blood_ff, blood_fm, blood_m, blood_mf, blood_mm, horse_title, check_flg, retired_flg, review_cource_left_text, review_cource_left, review_cource_right, review_cource_right_text, review_distance_left_text, review_distance_left, review_distance_right, review_distance_right_text, review_style_left_text, review_style_left, review_style_right, review_style_right_text, review_grow_left_text, review_grow_left, review_grow_right, review_grow_right_text, review_heavy_left_text, review_heavy_left, review_heavy_right, review_heavy_right_text)')
        cur.execute('CREATE TABLE race_info(horse_id, race_id, date, venue, horse_num, post_position, horse_number, odds, fav, result, jockey_id, burden_weight, distance, course_condition, time, margin, corner_pos, pace, last_3f, prize, grade, PRIMARY KEY(horse_id, race_id))')
        cur.execute('CREATE TABLE race_result(horse_id, race_id, race_name, grade, race_data1, race_data2, post_position, burden_weight, time, margin, horse_weight, prize, result, PRIMARY KEY(horse_id, race_id))')
        cur.execute('CREATE TABLE jockey_info(jockey_id, year, num, PRIMARY KEY(jockey_id, year))')
        conn.commit()

        cur.close()
        conn.close()

    def __del__(self):
        # データベースへのコネクションを閉じる
        self.cur.close()
        self.conn.close()

    # DBをRAM上に移して、以降の操作をRAM上で行う
    def _switch_RAM(self):
        # RAM DBへのコネクション作成
        dest = sqlite3.connect(':memory:')
        self.conn.backup(dest)
        # ROM DBへのコネクションを閉じる
        self.cur.close()
        self.conn.close()
        # コネクション変数譲渡
        self.conn = dest
        # sqliteを操作するカーソルオブジェクトを作成
        self.cur = self.conn.cursor()

    def sql_mul_all(self, table_name):
        """table要素をすべて取得する
        テーブルの要素数に注意"""
        sql = "SELECT * FROM {0};".format(table_name)
        self.cur.execute(sql)
        return self.cur.fetchall()

    def sql_one_horse_prof(self, horse_id, col_name):
        # horse_prof テーブルから指定列の要素を一つ取り出す
        # 主キーを指定するため必ず1つに絞れる
        sql = "SELECT " + col_name + " FROM horse_prof WHERE horse_id=?;"
        self.cur.execute(sql, [horse_id])
        return self.cur.fetchone()[0]

    def sql_one_race_info(self, race_id, horse_id, col_name):
        # race_info テーブルから指定列の要素を一つ取り出す
        # 主キーを指定するため必ず1つに絞れる
        sql = "SELECT " + col_name + " FROM race_info WHERE race_id=? AND horse_id=?;"
        self.cur.execute(sql, [race_id, horse_id])
        return self.cur.fetchone()[0]

    def sql_one_race_result(self, race_id, horse_id, col_name):
        # race_result テーブルから指定列の要素を一つ取り出す
        # 主キーを指定するため必ず1つに絞れる
        sql = "SELECT " + col_name + " FROM race_result WHERE race_id=? AND horse_id=?;"
        self.cur.execute(sql, [race_id, horse_id])
        data = self.cur.fetchone()
        if data is None:
            return None
        else:
            return data[0]

    def sql_mul_tbl(self, table_name, col_target_list, col_hint_list, data_list):
        # テーブル table_name から列 col_target を複数取得する
        # 条件は 列 col_hint_list と値  data_list が一致する行
        col_hint_list_copied = copy.copy(col_hint_list)
        for idx in range(len(col_hint_list_copied)):
            col_hint_list_copied[idx] = col_hint_list_copied[idx] + " =?"

        sql = "SELECT " + ','.join(col_target_list) + " FROM " + table_name + " WHERE " + " AND ".join(col_hint_list_copied) + ";"
        self.cur.execute(sql, data_list)
        retList = []
        for i in self.cur.fetchall():
            if len(col_target_list) == 1:
                retList.append(i[0])
            else:
                retList.append(i)

        return retList

    def sql_mul_tbl_g1g2g3(self, table_name, col_target_list, col_hint_list, data_list):
        # 重賞のみを対象とした
        # テーブル table_name から列 col_target を複数取得する
        # 条件は 列 col_hint_list と値  data_list が一致する行
        col_hint_list_copied = copy.copy(col_hint_list)
        for idx in range(len(col_hint_list_copied)):
            col_hint_list_copied[idx] = col_hint_list_copied[idx] + " =?"

        sql = "SELECT " + ','.join(col_target_list) + " FROM " + table_name + " WHERE " + " AND ".join(col_hint_list_copied) + " AND (grade=\"1\" OR grade=\"2\" OR grade=\"3\" OR grade=\"6\" OR grade=\"7\" OR grade=\"8\");"
        self.cur.execute(sql, data_list)
        retList = []
        for i in self.cur.fetchall():
            if len(col_target_list) == 1:
                retList.append(i[0])
            else:
                retList.append(i)

        return retList

    def sql_one_rowCnt(self, table_name, col_name, data):
        # テーブル table_name の 列 col_name が 値 data である行数を返す

        # COUNTは!NULLレコード数を返すため, 条件に OR NULL を付加する
        sql = "SELECT COUNT(" + col_name + "=? OR NULL) FROM " + table_name + ";"
        self.cur.execute(sql, [data])
        return int(self.cur.fetchone()[0])

    def sql_one_rowCnt_range(self, table_name, col_name, data, lower, upper):
        # テーブル table_name の 列 col_name が 値 data である行数を返す(条件 : lower <= race_id <= upper)
        # COUNTは!NULLレコード数を返すため, 条件に OR NULL を付加する
        sql = "SELECT COUNT(" + col_name + "=? OR NULL) FROM " + table_name + " WHERE ((race_id <= \"" + upper + "\") AND (race_id >= \""+ lower + "\"));"
        self.cur.execute(sql, [data])
        return int(self.cur.fetchone()[0])

    def sql_one_jockey_total(self, jockey_id, lower, upper):
        # 指定騎手の騎乗回数をfloatで返す
        sql = "SELECT TOTAL(num) FROM jockey_info WHERE ((jockey_id = \"" + jockey_id +"\" ) AND ( year BETWEEN \"" + lower + "\" AND \"" + lower + "\" ));"
        self.cur.execute(sql)
        return self.cur.fetchone()[0]

    def sql_mul_distinctColCnt_G1G2G3(self, lower, upper, limit):
        # !!注意!! ソートは行っていないので必ず lower から順に limit 件取り出しているとは限らない
        # DISTINCT を使用して
        # 芝, ダートの G1, G2, G3 のレースIDを取り出す
        # (条件に使われる数字はstring2grade()のコメント参照)
        # 検索範囲 lower <= data <= upper
        # limit 取り出し件数
        table_name = "race_result"
        col_name   = "race_id"
        sql = "SELECT DISTINCT " + col_name + " FROM " + table_name + " WHERE (" + col_name + " <= \""+ upper +"\") AND (" + col_name + " >= \""+ lower + "\") AND (grade=\"1\" OR grade=\"2\" OR grade=\"3\" OR grade=\"6\" OR grade=\"7\" OR grade=\"8\") LIMIT "+ str(limit) + ";"
        self.cur.execute(sql)
        retList = []
        for i in self.cur.fetchall():
            retList.append(i[0])
        return retList

    def sql_mul_sortHorseNum(self, target_col_list, hint_col, data):
        # 複数テーブルから内部結合(inner join)してから指定列を取り出す
        # SQLite はレコードの順序保証はないため、馬番で昇順ソートを行う
        # 順序保証が必要な場合この関数を使用すること
        # target_col_list : 取得したい列。テーブル名から明記すること。 ex : ["race_info.result"]
        # hint_col        : 検索条件の列名。テーブル名から明記すること。 ex : "race_info.race_id"
        # data            : 検索条件のデータ。 hint_col 列から一致したdataのある行のみ取り出すことになる。

        # race_info.horse_number に +0 してあるのはテーブルの管理上 文字列の列を数値にキャストするため
        sql = "SELECT " + ','.join(target_col_list) + " FROM race_info INNER JOIN race_result ON (race_result.race_id = race_info.race_id AND race_result.horse_id = race_info.horse_id) WHERE " + hint_col + " = ? ORDER BY race_info.horse_number + 0;"
        self.cur.execute(sql, [data])
        retList = []
        for i in self.cur.fetchall():
            retList.append(i[0])
        return retList

    def sql_mul_race_id_1v1(self, horse1, horse2):
        # horse1, horse2 両方が出たレースIDを返す
        sql = "SELECT race_info.race_id FROM (SELECT horse_id, race_id, result, COUNT(race_id) AS CNT FROM race_info WHERE (horse_id=? OR horse_id=?) GROUP BY race_id) AS race_sum INNER JOIN race_info ON race_info.horse_id = race_sum.horse_id AND race_info.race_id = race_sum.race_id AND race_sum.CNT > 1;"
        self.cur.execute(sql, [horse1, horse2])
        retList = []
        for i in self.cur.fetchall():
            retList.append(i[0])
        return retList

    def sql_mul_diff(self, table1, col1, table2, col2):
        """col1 - col2 を返す
        重複しているcolの要素は1つとみなす"""

        sql = "SELECT DISTINCT {0} FROM {1} EXCEPT SELECT DISTINCT {2} FROM {3};".format(col1, table1, col2, table2)
        self.cur.execute(sql)
        result  = self.cur.fetchall()
        # logger.info("col1 - col2 = {0}".format(result))
        retList = []
        for i in result:
            retList.append(i[0])
        return retList

    def sql_isIn(self, tbl_name, condition_list):
        """テーブル内に条件に一致する行が存在するか判定
        tbl_name: テーブル名
        condition_list: 条件リスト (例) ["horse_id='1983103914'"]
        """
        sql = "SELECT * FROM {} WHERE ".format(tbl_name) + " AND ".join(condition_list) + " LIMIT 1"
        self.cur.execute(sql)
        search_result = self.cur.fetchall()
        if len(search_result) == 0:
            return False
        else:
            return True

    def sql_insert_RowToRaceId(self, race_id_list):
        # race_idテーブルに新しい行を挿入
        for race_id in race_id_list:
            sql = "INSERT INTO race_id(id) values('{}')".format(race_id)
            self.cur.execute(sql)
        self.conn.commit()

    def sql_insert_RowToUntrackedRaceId(self, race_id_list):
        # untracked_race_idテーブルに新しい行を挿入
        for race_id in race_id_list:
            if self.sql_isIn("untracked_race_id", ["race_id='{0}'".format(race_id)]) == False:
                sql = "INSERT INTO untracked_race_id(race_id) values('{}')".format(race_id)
                self.cur.execute(sql)
        self.conn.commit()

    def sql_insert_RowToUntrackedHorseId(self, horse_id_list):
        # untracked_horse_idテーブルに新しい行を挿入
        for horse_id in horse_id_list:
            if self.sql_isIn("untracked_horse_id", ["horse_id='{0}'".format(horse_id)]) == False:
                sql = "INSERT INTO untracked_horse_id(horse_id) values('{}')".format(horse_id)
                self.cur.execute(sql)
        self.conn.commit()

    def sql_insert_Row(self, tbl_name, target_col_list, data_list):
        """テーブルに新しい行を挿入
        tbl_name: テーブル名
        target_col_list: 列の指定
        data: 挿入するデータ.2次元配列で指定.全ての要素で列数が同じ.(全部文字列になる)
        """
        for data in data_list:
            for i in range(len(data)):
                # シングルクォーテーションのエスケープ処理
                if "'" in data[i]:
                    data[i] = data[i].replace("'", "''")
            # データの文字列化
            data_modified = list(map(lambda x: "'" + str(x) + "'", data))
            val_str = ",".join(data_modified)

            sql = "INSERT INTO {}(".format(tbl_name) + ",".join(target_col_list) + ") values(" + val_str + ")"
            self.cur.execute(sql)
        self.conn.commit()

    def sql_update_Row(self, tbl_name, target_col_list, data_list, condition=[]):
        """テーブルのデータを更新
        data: 更新するデータ．2次元配列で指定． 全ての要素で列数が同じ．(全部文字列になる)
        conditon: 条件式がない場合は[]
        """

        target_col_list_copied = copy.copy(target_col_list)
        for i in range(len(target_col_list_copied)):
            target_col_list_copied[i] = target_col_list_copied[i] + "=?"

        for data in data_list:
            # シングルクォーテーションのエスケープ処理
            for i in range(len(data)):
                if "'" in data[i]:
                    data[i] = data[i].replace("'", "''")

            if condition == []:
                sql = "UPDATE {} SET ".format(tbl_name) + ",".join(target_col_list_copied)
            else:
                sql = "UPDATE {} SET ".format(tbl_name) + ",".join(target_col_list_copied) + " WHERE " + " AND ".join(condition)
            self.cur.execute(sql, data)

        self.conn.commit()

    def sql_del_row(self, table_name, key_name_list, key_data_list):
        """指定テーブルから行を削除する。行の指定にはキーを使う"""
        sql = "DELETE FROM " + table_name + " WHERE "

        add_place_holder = []
        for key_name in key_name_list:
            add_place_holder.append(key_name + "=?")
        sql += ' AND '.join(add_place_holder)
        sql += ';'

        # print(sql)

        self.cur.execute(sql, key_data_list)
        self.conn.commit()
