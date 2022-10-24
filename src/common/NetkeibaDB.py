# Netkeiba.py
# DBにアクセスするためSQL発行して結果を加工して返す

# 関数命名ルール
# sql_{A}_{B}()
# {A} = one | mul
# one : 取得する行数が必ず1つ
# mul : 取得する行数が1つ以上
# {B} = 関数名

import sqlite3

from debug import *

class NetkeibaDB:
    def __init__(self, path_db):
        logger.info("Database {0} loading".format(path_db))
        self.conn = sqlite3.connect(path_db)
        # sqliteを操作するカーソルオブジェクトを作成
        self.cur = self.conn.cursor()
        logger.info("Database {0} loading complete".format(path_db))

    def __del__(self):
        # データベースへのコネクションを閉じる
        self.cur.close()
        self.conn.close()

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
        return self.cur.fetchone()[0]

    def sql_mul_tbl(self, table_name, col_target_list, col_hint_list, data_list):
        # テーブル table_name から列 col_target を複数取得する
        # 条件は 列 col_hint_list と値  data_list が一致する行
        for idx in range(len(col_hint_list)):
            col_hint_list[idx] = col_hint_list[idx] + " =?"

        sql = "SELECT " + ','.join(col_target_list) + " FROM " + table_name + " WHERE " + " AND ".join(col_hint_list) + ";"
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

    def sql_mul_distinctColCnt(self, table_name, col_name, lower, upper, limit):
        # 指定列のデータを全て取得しリストで返す
        # ただし重複データは1つになる
        # 検索範囲 lower <= data <= upper
        # limit 取り出し件数
        sql = "SELECT DISTINCT " + col_name + " FROM " + table_name + " WHERE " + col_name + " <= \""+ upper +"\" AND " + col_name + " >= \""+ lower + "\" limit "+ str(limit) + ";"
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

    def sql_insert_RowToRaceId(self, race_id_list):
        # race_idテーブルに新しい行を挿入
        for race_id in race_id_list:
            sql = "INSERT INTO race_id(id) values('{}')".format(race_id)
            self.cur.execute(sql)
        self.conn.commit()

    def sql_insert_Row(self, tbl_name, target_col_list, data_list):
        """テーブルに新しい行を挿入
        tbl_name: テーブル名
        target_col_list: 列の指定
        data: 挿入するデータ．全ての要素で列数が同じ．2次元配列で指定． (全部文字列になる)
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
            print(sql)
            self.cur.execute(sql)
        self.conn.commit()

    def sql_update_Row(self, tbl_name, target_col_list, data_list, condition=[]):
        """テーブルのデータを更新
        data: 更新するデータ．全ての要素で列数が同じ．2次元配列で指定． (全部文字列になる)
        conditon: 条件式がない場合は[]
        """

        for i in range(len(target_col_list)):
            target_col_list[i] = target_col_list[i] + "=?"
        
        for data in data_list:
            # シングルクォーテーションのエスケープ処理
            for i in range(len(data)):
                if "'" in data[i]:
                    data[i] = data[i].replace("'", "''")
                
            if condition == []:
                sql = "UPDATE {} SET ".format(tbl_name) + ",".join(target_col_list)
            else:
                sql = "UPDATE {} SET ".format(tbl_name) + ",".join(target_col_list) + " WHERE " + " AND ".join(condition)
            self.cur.execute(sql, data)

        self.conn.commit()
