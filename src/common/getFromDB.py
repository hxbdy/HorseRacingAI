import os
import sys
import logging
import sqlite3
import pathlib
from datetime import date
from dateutil.relativedelta import relativedelta

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
