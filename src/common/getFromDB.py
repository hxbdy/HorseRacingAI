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

from common.NetkeibaDB import *

db = NetkeibaDB()

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

def getTotalRaceList(year = "999999999999"):
    # yearを含む年のレースまでを全て取得する
    # デフォルトでは全てのレースを取得する
    # DB上のrace_idの上4桁は開催年前提
    if year != "999999999999":
        year = str(year) + "99999999"
    totalRaceList = db.getDistinctCol("race_result", "race_id", year)
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
    