import sys
import pathlib
from datetime import date
import re

# commonフォルダ内読み込みのため
deepLearning_dir = pathlib.Path(__file__).parent
src_dir = deepLearning_dir.parent
root_dir = src_dir.parent
dir_lst = [deepLearning_dir, src_dir, root_dir]
for dir_name in dir_lst:
    if str(dir_name) not in sys.path:
        sys.path.append(str(dir_name))

from NetkeibaDB import db
from debug import *

def getCourseCondition(race_id):
    raceData1List = db.getColDataFromTbl("race_result", "race_data1", "race_id", race_id)
    # コース状態取得
    # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
    sep1 = raceData1List[0].split(":")[2]
    #  良 / 発走 
    sep1 = sep1.split("/")[0]
    # 良
    sep1 = sep1.replace(" ", "")
    return sep1

def getTotalRaceList(start_year = 0, end_year = 9999):
    # yearを含む年のレースまでを全て取得する
    # デフォルトでは全てのレースを取得する
    # DB上のrace_idの上4桁は開催年前提
    if len(str(start_year)) != 4:
        logger.critical("len(str(start_year)) != 4")
        start_year = "0000"
    if len(str(end_year)) != 4:
        logger.critical("len(str(end_year)) != 4")
        end_year = "9999"
    start_year = str(start_year) + "00000000"
    end_year   = str(end_year)   + "99999999"
    totalRaceList = db.getDistinctCol("race_result", "race_id", start_year, end_year)
    return totalRaceList

def getRaceDate(race_id):
    # レース開催日を取り出す
    # 以下の前提で計算する
    # race_data2 にレース開催日が含まれていること
    raceDate = db.getColDataFromTbl("race_result", "race_data2", "race_id", race_id)
    raceDate = raceDate[0]
    raceDateYear = int(raceDate.split("年")[0])
    raceDateMon = int(raceDate.split("年")[1].split("月")[0])
    raceDateDay = int(raceDate.split("月")[1].split("日")[0])
    return date(raceDateYear, raceDateMon, raceDateDay)

#def calCumNumOfWin(horsedb):
    # 累計勝利数を計算
    # horsedb.cum_num_wins = []
    # for horse_perform in horsedb.perform_contents:
    #     cum_win_list = []
    #     cum_win = 0
    #     horse_perform.reverse()
    #     for race_result in horse_perform:
    #         if race_result[8] == '1':
    #             cum_win += 1
    #         cum_win_list.append(cum_win)
    #     cum_win_list.reverse()
    #     horsedb.cum_num_wins.append(cum_win_list)

#def calCumMoney(horsedb):
    # 累計獲得賞金を計算
    # horsedb.cum_money = []
    # for horse_perform in horsedb.perform_contents:
    #     cum_money_list = []
    #     cum_money = 0.0
    #     horse_perform.reverse()
    #     for race_result in horse_perform:
    #         if race_result[15] == ' ':
    #             money = 0.0
    #         else:
    #             money = float(race_result[15].replace(",",""))
    #         cum_money += money
    #         cum_money_list.append(cum_money)
    #     cum_money_list.reverse()
    #     horsedb.cum_money.append(cum_money_list)
