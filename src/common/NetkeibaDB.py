import os
import sys
import logging
import sqlite3
import pathlib

# commonフォルダ内読み込みのため
deepLearning_dir = pathlib.Path(__file__).parent
src_dir = deepLearning_dir.parent
root_dir = src_dir.parent
dir_lst = [deepLearning_dir, src_dir, root_dir]
for dir_name in dir_lst:
    if str(dir_name) not in sys.path:
        sys.path.append(str(dir_name))

from common.debug import *

class NetkeibaDB:
    def __init__(self):
        logger.info("Database loading")
        self.dbpath = str(root_dir) + '\\dst\\netkeibaDB\\netkeiba.db'
        self.conn = sqlite3.connect(self.dbpath)
        # sqliteを操作するカーソルオブジェクトを作成
        self.cur = self.conn.cursor()
        logger.info("Database loading complete")

    def __del__(self):
        # データベースへのコネクションを閉じる
        self.cur.close()
        self.conn.close()

    def horse_prof_getOneData(self, horse_id, col_name):
        # horse_prof テーブルから指定列の要素を一つ取り出す
        # 主キーを指定するため必ず1つに絞れる
        sql = "SELECT " + col_name + " FROM horse_prof WHERE horse_id=?;"
        self.cur.execute(sql, [horse_id])
        return self.cur.fetchone()[0]

    def race_info_getOneData(self, race_id, horse_id, col_name):
        # race_info テーブルから指定列の要素を一つ取り出す
        # 主キーを指定するため必ず1つに絞れる
        sql = "SELECT " + col_name + " FROM race_info WHERE race_id=? AND horse_id=?;"
        self.cur.execute(sql, [race_id, horse_id])
        return self.cur.fetchone()[0]

    def race_result_getOneData(self, race_id, horse_id, col_name):
        # race_result テーブルから指定列の要素を一つ取り出す
        # 主キーを指定するため必ず1つに絞れる
        sql = "SELECT " + col_name + " FROM race_result WHERE race_id=? AND horse_id=?;"
        self.cur.execute(sql, [race_id, horse_id])
        return self.cur.fetchone()[0]

    def getRecordDataFromTbl(self, table_name, col_name, data):
        # 指定テーブルから列と値が一致する行をリストで返す
        sql = "SELECT * FROM " + table_name + " WHERE " + col_name + " =?;"
        self.cur.execute(sql, [data])
        retList = []
        for i in self.cur.fetchall():
            retList.append(i[0])
        return retList

    def getColDataFromTbl(self, table_name, col_target, col_hint, data):
        # 指定テーブルから列と値が一致する行をリストで返す
        sql = "SELECT " + col_target + " FROM " + table_name + " WHERE " + col_hint + " =?;"
        self.cur.execute(sql, [data])
        retList = []
        for i in self.cur.fetchall():
            retList.append(i[0])
        return retList

    def getRowCnt(self, table_name, col_name, data):
        # テーブルtable_name の 列col_name が 値data である行数を返す
        # COUNTは!NULLのレコード数を返すため条件に OR NULL を付加する
        sql = "SELECT COUNT(" + col_name + "=? OR NULL) FROM " + table_name + ";"
        self.cur.execute(sql, [data])
        return int(self.cur.fetchone()[0])

    def getDistinctCol(self, table_name, col_name, lower, upper):
        # 指定列のデータを全て取得しリストで返す
        # ただし重複データは1つになる
        # 検索範囲 lower <= data <= upper
        sql = "SELECT DISTINCT " + col_name + " FROM " + table_name + " WHERE " + col_name + " <= \""+ upper +"\" AND " + col_name + " >= \""+ lower + "\";"
        self.cur.execute(sql)
        retList = []
        for i in self.cur.fetchall():
            retList.append(i[0])
        return retList

    def getMulCol(self, table_name, target_col_list, col_hint, data):
        # 指定テーブルから複数の指定列を取り出したレコードを返す
        sql = "SELECT " + ','.join(target_col_list) + " FROM " + table_name + " WHERE " + col_hint + " =?;"
        self.cur.execute(sql, [data])
        retList = []
        for i in self.cur.fetchall():
            retList.append(i)
        return retList

    def getMulColOrderByHorseNum(self, target_col_list, hint_col, data):
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

    def getRaceIdFromHorseId(self, horse1, horse2):
        # horse1, horse2 両方が出たレースIDを返す
        sql = "SELECT race_info.race_id FROM (SELECT horse_id, race_id, result, COUNT(race_id) AS CNT FROM race_info WHERE (horse_id=? OR horse_id=?) GROUP BY race_id) AS race_sum INNER JOIN race_info ON race_info.horse_id = race_sum.horse_id AND race_info.race_id = race_sum.race_id AND race_sum.CNT > 1;"
        self.cur.execute(sql, [horse1, horse2])
        retList = []
        for i in self.cur.fetchall():
            retList.append(i[0])
        return retList
    
db = NetkeibaDB()
