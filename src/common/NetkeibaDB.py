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

    def getDistinctCol(self, table_name, col_name):
        # 指定列のデータを全て取得しリストで返す
        # ただし重複データは1つになる
        sql = "SELECT DISTINCT " + col_name + " FROM " + table_name + ";"
        self.cur.execute(sql)
        retList = []
        for i in self.cur.fetchall():
            retList.append(i[0])
        return retList
