# ./dst/scrapingResult/horsedb.pickle, racedb.pickle から
# ./dst/netkeibaDB/netkeiba.db へ変換する
# テーブルの形については ./doc/テーブル.txt 参照

import pickle
import sys
import pathlib
import logging
import sqlite3

# commonフォルダ内読み込みのため
deepLearning_dir = pathlib.Path(__file__).parent
src_dir = deepLearning_dir.parent
root_dir = src_dir.parent
dir_lst = [deepLearning_dir, src_dir, root_dir]
for dir_name in dir_lst:
    if str(dir_name) not in sys.path:
        sys.path.append(str(dir_name))

from common.HorseDB import HorseDB
from common.RaceDB import RaceDB
from common.RaceGradeDB import RaceGradeDB

def insert_horse_prof_table(dbname, horsedb):
    logger.info("INSERT INTO horse_prof VALUES start")

    conn = sqlite3.connect(dbname)
    cur = conn.cursor()

    # horse_prof テーブルの列数
    # recordリストにおける募集情報のインデックス
    TABLE_SIZE = 18
    place_holder = ','.join(['?'] * TABLE_SIZE)

    DELETE_RECORD_IDX = 4
    HORSE_ID_LEN = len(horsedb.horseID)

    sql = "INSERT INTO horse_prof VALUES(" + place_holder + ");"

    for i in range(HORSE_ID_LEN):
        
        record = [horsedb.horseID[i], *horsedb.prof_contents[i], *horsedb.blood_list[i], horsedb.check[i]]
        
        # DBと列数が同じかチェックする
        # horsedb.prof_contents[] に募集情報がある時削除する
        if len(record) != TABLE_SIZE:
            logger.info("POP index https://db.netkeiba.com/horse/{0}".format(horsedb.horseID[i]))
            record.pop(DELETE_RECORD_IDX)
            if len(record) != TABLE_SIZE:
                logger.critical("invalid insert record size : input = {0}, database = {1}".format(len(record), TABLE_SIZE))
            
        logger.debug("INSERT INTO horse_prof VALUES {0}".format(record))

        cur.execute(sql, record)
        conn.commit()

        logger.info("insert_horse_prof_table / status {0}/{1}".format(i, HORSE_ID_LEN))

    cur.close()
    conn.close()

    logger.info("INSERT INTO horse_prof VALUES end")

def insert_race_info_table(dbname, horsedb, rgdb):
    logger.info("INSERT INTO race_info VALUES start")

    conn = sqlite3.connect(dbname)
    cur = conn.cursor()

    # race_info テーブルの列数
    TABLE_SIZE = 18
    place_holder = ','.join(['?'] * TABLE_SIZE)
    # horsedb.perform_contents 上のレースIDインデックス
    RACE_ID_IDX = 2
    HORSE_ID_LEN = len(horsedb.horseID)
    sql = "INSERT INTO race_info VALUES(" + place_holder + ");"

    for i in range(HORSE_ID_LEN):
        for j in horsedb.perform_contents[i]:
            # レースIDを先頭へ移動
            race_id = j[RACE_ID_IDX]
            j.pop(RACE_ID_IDX)
            record = [horsedb.horseID[i], race_id, *j, rgdb.getGrade(race_id)]

            logger.debug("INSERT INTO race_info VALUES {0}".format(record))

            cur.execute(sql, record)
            conn.commit()

        logger.info("insert_race_info_table / status {0}/{1}".format(i, HORSE_ID_LEN))

    cur.close()
    conn.close()

    logger.info("INSERT INTO race_info VALUES end")

def insert_race_result_table(dbname, racedb):
    logger.info("INSERT INTO race_result VALUES start")

    conn = sqlite3.connect(dbname)
    cur = conn.cursor()

    # race_info テーブルの列数
    TABLE_SIZE = 9
    place_holder = ','.join(['?'] * TABLE_SIZE)
    RACE_ID_LEN = len(racedb.raceID)

    sql = "INSERT INTO race_result VALUES(" + place_holder + ");"

    for i in range(RACE_ID_LEN):
        for j in range(len(racedb.horseIDs_race[i])):
            record = [racedb.horseIDs_race[i][j], racedb.raceID[i], racedb.race_name[i], racedb.race_data1[i], racedb.race_data2[i], racedb.goal_time[i][j], racedb.goal_dif[i][j], racedb.horse_weight[i][j], racedb.money[i][j]]
            logger.debug("INSERT INTO race_result VALUES {0}".format(record))
            cur.execute(sql, record)
            conn.commit()
        logger.info("insert_race_result_table / status {0}/{1}".format(i, RACE_ID_LEN))

    cur.close()
    conn.close()

    logger.info("INSERT INTO race_result VALUES end")

if __name__ == "__main__":
    # debug initialize
    # LEVEL : DEBUG < INFO < WARNING < ERROR < CRITICAL
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s [%(levelname)s] %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logging.disable(logging.DEBUG)

    # pickle読み込み
    logger.info("Pickle Database loading")

    # レース情報読み込み
    with open(str(root_dir) + "\\dst\\scrapingResult\\racedb.pickle", 'rb') as f:
            racedb = pickle.load(f)

    # 馬情報読み込み
    with open(str(root_dir) + "\\dst\\scrapingResult\\horsedb.pickle", 'rb') as f:
            horsedb = pickle.load(f)

    # レースグレード情報読み込み
    with open(str(root_dir) + "\\dst\\scrapingResult\\raceGradedb.pickle", 'rb') as f:
            rgdb = pickle.load(f)

    logger.info("Pickle Database loading complete")

    dbname = '.\\dst\\netkeibaDB\\netkeiba.db'
    insert_horse_prof_table(dbname, horsedb)
    insert_race_info_table(dbname, horsedb, rgdb)
    insert_race_result_table(dbname, racedb)
