from dateutil.relativedelta import relativedelta
from common.getFromDB import *

def fixBirthDayList(args):
    # 標準化の前に誕生日を日数表記にしておく
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
    # 騎手の総出場回数を求める
    jockeyIDList = args[0]
    for i in range(len(jockeyIDList)):
        jockeyIDList[i] = getJockeyCnt(jockeyIDList[i])
    return jockeyIDList

def fixWeatherList(args):
    return args[0]

def fixCourseConditionList(args):
    return args[0]

def fixRaceStartTimeList(args):
    return args[0]

def fixCourseDistanceList(args):
    return args[0]

def fixMoneyList(args):
    # 賞金リストをfloat変換する
    rowList = args[0]
    moneyList = []
    for m in rowList:
        if m == "":
            fm = "0.0"
        else:
            fm = m.replace(",","")
        moneyList.append(float(fm))
    return moneyList

def fixHorseNumList(args):
    return args[0]

def fixMarginList(args):
    # 着差をfloatにして返す
    # 着差の種類は以下の通り。これ以外は存在しない。
    # 同着 - 写真によっても肉眼では差が確認できないもの - タイム差は0 = 0
    # ハナ差（鼻差） - スリットの数は3 - タイム差は0 = 0.0125
    # アタマ差（頭差） - スリットの数は6 - タイム差は0 = 0.025
    # クビ差（首差、頸差） - スリットの数は12 - タイム差は0〜1/10秒 = 0.05
    # 1/2馬身（半馬身） - スリットの数は24 - タイム差は1/10秒 = 0.1
    # 3/4馬身 - スリットの数は30 - タイム差は1/10〜2/10秒 = 0.15
    # 1馬身 - スリットの数は33 - タイム差は2/10秒 = 0.2
    # 1 1/4馬身（1馬身と1/4） - スリットの数は37 - タイム差は2/10秒 = 0.2
    # 1 1/2馬身（1馬身と1/2） - タイム差は2/10〜3/10秒 = 0.25
    # 1 3/4馬身（1馬身と3/4） - タイム差は3/10秒 = 0.3
    # 2馬身 - タイム差は3/10秒 = 0.3
    # 2 1/2馬身 - タイム差は4/10秒 =  0.4
    # 3馬身 - タイム差は5/10秒 = 0.5
    # 3 1/2馬身 - タイム差は6/10秒 = 0.6
    # 4馬身 - タイム差は7/10秒 = 0.7
    # 5馬身 - タイム差は8/10〜9/10秒 = 0.9
    # 6馬身 - タイム差は1秒 = 1.0
    # 7馬身 - タイム差は11/10〜12/10秒 = 1.2
    # 8馬身 - タイム差は13/10秒 = 1.3
    # 9馬身 - タイム差は14/10〜15/10秒 = 1.5
    # 10馬身 - タイム差は16/10秒   = 1.6
    # 大差 - タイム差は17/10秒以上 = 1.7
    # ['', '5', '2', '2', '1.1/4', '5', '1', '9']
    marginDict = {'同着':0, '':0, 'ハナ':0.0125, 'アタマ':0.025, 'クビ':0.05, '1/2':0.1, '3/4':0.15, '1':0.2, \
                  '1.1/4':0.2, '1.1/2':0.25, '1.3/4':0.3, '2':0.3, '2.1/2':0.4, '3':0.5, '3.1/2':0.6, '4':0.7, '5':0.9, \
                  '6':1.0, '7':1.2, '8':1.3, '9':1.5, '10':1.6, '大':1.7}
    time = 0
    retList = []
    for i in range(len(args[0])):
        margin = args[0][i]
        # 'クビ+1/2' などの特殊な表記に対応する
        if '+' in margin:
            m = margin.split('+')
            time += marginDict[m[0]]
            time += marginDict[m[1]]
        else:
            time += marginDict[margin]
        retList.append(time)
    return retList
