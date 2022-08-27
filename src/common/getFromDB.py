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

def getBurdenWeightList(race_id):
    burdenWeightList = db.getColDataFromTbl("race_info", "burden_weight", "race_id", race_id)
    for i in range(len(burdenWeightList)):
        burdenWeightList[i] = float(burdenWeightList[i])
    return burdenWeightList

def getPostPositionList(race_id):
    postPositionList = db.getColDataFromTbl("race_info", "post_position", "race_id", race_id)
    for i in range(len(postPositionList)):
        postPositionList[i] = float(postPositionList[i])
    return postPositionList

def getJockeyCnt(jockey_id):
    cnt = db.getRowCnt("race_info", "jockey_id", jockey_id)
    return cnt

def getJockeyIDList(race_id):
    jockeyIDList = db.getColDataFromTbl("race_info", "jockey_id", "race_id", race_id)
    for i in range(len(jockeyIDList)):
        jockeyIDList[i] = str(jockeyIDList[i])
    return jockeyIDList

def getBirthDayList(race_id):
    horseList = db.getColDataFromTbl("race_info", "horse_id", "race_id", race_id)
    bdList = []
    for horse_id in horseList:
        data = db.horse_prof_getOneData(horse_id, "bod")
        birthYear = int(data.split("年")[0])
        birthMon = int(data.split("年")[1].split("月")[0])
        birthDay = int(data.split("月")[1].split("日")[0])
        d1 = date(birthYear, birthMon, birthDay)
        bdList.append(d1)
    return bdList

def getWeather(race_id):
    raceData1List = db.getColDataFromTbl("race_result", "race_data1", "race_id", race_id)
    sep1 = raceData1List[0].split(":")[1]
    #  晴 / 芝 
    sep1 = sep1.split("/")[0]
    # 晴 
    sep1 = sep1.replace(" ", "")
    return sep1

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

def getRaceStartTimeList(race_id):
    raceData1List = db.getColDataFromTbl("race_result", "race_data1", "race_id", race_id)
    # 出走時刻取得
    # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
    sep1 = raceData1List[0].split("/")[3]
    #  発走 : 15:35
    sep1 = sep1.split(" : ")[1]
    #  15:35
    sep1 = sep1.replace(" ", "")
    # 他と統一するためリストにする
    return [sep1]

def getCourseDistanceList(race_id):
    raceData1List = db.getColDataFromTbl("race_result", "race_data1", "race_id", race_id)
    # 距離取得
    # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
    sep1 = raceData1List[0].split(":")[0]
    # 芝右1600m
    # 数字以外を削除
    sep1 = re.sub(r'\D', '', sep1)
    sep1 = sep1.replace(" ", "")
    # 他と統一するためリストにする
    return [float(sep1)]

def getMoneyList(race_id):
    prizeList = db.getColDataFromTbl("race_result", "prize", "race_id", race_id)
    for i in range(len(prizeList)):
        prizeList[i] = str(prizeList[i])
    return prizeList

def getHorseNumList(race_id):
    # 他と統一するためリストにする
    return [db.getRowCnt("race_result", "race_id", race_id)]

def getMarginList(race_id):
    marginList = db.getColDataFromTbl("race_result", "margin", "race_id", race_id)
    for i in range(len(marginList)):
        marginList[i] = str(marginList[i])
    return marginList

def getTotalRaceList():
    totalRaceList = db.getDistinctCol("race_result", "race_id")
    return totalRaceList

def getRaceDateList(race_id):
    # レース開催日を取り出す
    # 以下の前提で計算する
    # race_data2 にレース開催日が含まれていること
    raceDate = db.getColDataFromTbl("race_result", "race_data2", "race_id", race_id)
    raceDate = raceDate[0]
    raceDateYear = int(raceDate.split("年")[0])
    raceDateMon = int(raceDate.split("年")[1].split("月")[0])
    raceDateDay = int(raceDate.split("月")[1].split("日")[0])
    return date(raceDateYear, raceDateMon, raceDateDay)

def getCumPerformList(race_id):
    # race_id に出場した馬のリストを取得
    # 各馬の以下情報を取得、fixでパフォーマンスを計算する
    col = ["horse_id", "venue", "time", "burden_weight", "course_condition", "distance", "grade"]
    horse_list = db.getRecordDataFromTbl("race_info", "race_id", race_id)
    horse_info_list = []
    for horse in horse_list:
        # horse の全てのレコードを取得
        race = db.getMulCol("race_info", col, "horse_id", horse)
        horse_info_list.append(race)
    return horse_info_list
