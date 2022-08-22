from dateutil.relativedelta import relativedelta
from common.getFromDB import *

def fixBirthDayList(args):
    bdList = args[0]
    d0 = args[1]
    for i in range(len(bdList)):
        dy = relativedelta(d0, bdList[i])
        age = dy.years + (dy.months / 12.0) + (dy.days / 365.0)
        bdList[i] = age
    return bdList

def fixBurdenWeightList(args):
    return args[0]

def fixPostPositionList(args):
    return args[0]

def fixJockeyIDList(args):
    jockeyIDList = args[0]
    for i in range(len(jockeyIDList)):
        jockeyIDList[i] = getJockeyCnt(jockeyIDList[i])
    return jockeyIDList

def fixWeatherList(args):
    return args[0]
