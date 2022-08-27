from dateutil.relativedelta import relativedelta
from common.getFromDB import *
import re

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

def getStandardTime(distance, condition, track, location):
    # レースコースの状態に依存する基準タイム(秒)を計算して返す
    # performancePredictionで予測した係数・定数を下の辞書の値に入れる．
    # loc_dictのOtherは中央競馬10か所以外の場合の値．10か所の平均値を取って作成する．
    dis_coef = 0.066433
    intercept = -9.6875
    cond_dict = {'良':-0.3145, '稍':0.1566, '重':0.1802, '不':-0.0223}
    track_dict = {'芝':-1.2514, 'ダ': 1.2514}
    loc_dict = {'札幌':1.1699, '函館':0.3113, '福島':-0.3205, '新潟':-0.2800, '東京':-0.8914,\
         '中山':0.2234, '中京':0.1815, '京都':-0.1556, '阪神':-0.4378, '小倉':0.1994, 'Other':0}
    
    std_time = dis_coef*distance + cond_dict[condition] + track_dict[track] + loc_dict[location] + intercept
    return std_time

def getPerformance(standard_time, goal_time, weight, grade):
    # 走破タイム・斤量などを考慮し，「強さ(performance)」を計算
    # 以下のeffectの値，計算式は適当
    weight_effect = 1+ (55 - weight)/1000
    grade_effect_dict = {'G1':1.14, 'G2':1.12, 'G3':1.10, 'OP':1.0, 'J.G1':1.0, 'J.G2':1.0, 'J.G3':1.0}
    perform = (10 + standard_time - goal_time*weight_effect) * grade_effect_dict[grade]
    return perform

def fixCumPerformList(args):
    # 各レースの結果から強さ(performance)を計算し，その最大値を記録していく
    # (外れ値を除くために，2番目の強さでもいいかもしれない．)
    # col = ["horse_id", "venue", "time", "burden_weight", "course_condition", "distance", "grade"]
    HORSE_ID         = 0
    VENUE            = 1
    TIME             = 2
    BURDEN_WEIGHT    = 3
    COURSE_CONDITION = 4
    DISTANCE         = 5
    GRADE            = 6
    loc_list = ['札幌', '函館', '福島', '新潟', '東京', '中山', '中京', '京都', '阪神', '小倉']
    max_performance_list = []

    for raw in args:
        # raw = [[(馬Aレースa情報), (馬Aレースb情報), ... ], [(馬Bレースc情報), (馬Bレースd情報), ...]]
        for race in raw:
            for horse_info in race:
                # horse_info = ('1982106916', '3小倉8', '1:12.7', '53', '良', '芝1200', '-1')
                max_performance = -1000.0
                # ゴールタイムを取得
                goaltime = horse_info[TIME]
                try:
                    goaltime_sec = float(goaltime.split(':')[0])*60 + float(goaltime.split(':')[1])
                except:
                    goaltime_sec = 240
                # 斤量を取得
                try:
                    burden_weight = float(horse_info[BURDEN_WEIGHT])
                except:
                    burden_weight = 40
                # 馬場状態を取得
                condition = horse_info[COURSE_CONDITION]
                # 競馬場を取得
                location = horse_info[VENUE]
                if location not in loc_list:
                    location = "Other"
                # 芝かダートか
                if horse_info[DISTANCE][0] == "芝":
                    track = "芝"
                elif horse_info[DISTANCE][0] == "ダ":
                    track = "ダ"
                else:
                    track = "E"
                # コースの距離
                dis_str = horse_info[DISTANCE]
                try:
                    distance = float(re.sub(r'\D', '', dis_str).replace(" ", ""))
                except:
                    distance = "E"
                # レースのグレード (G1,G2,G3,OP)
                # 日本の中央競馬以外のレースは全てOP扱いになる
                grade = horse_info[GRADE]
                if grade == "-1":
                    grade = "OP"
                else:
                    grade = "G" + grade
                # 計算不能な場合を除いてperformanceを計算
                if track != "E" and distance != "E":
                    standard_time = getStandardTime(distance, condition, track, location)
                    performance = getPerformance(standard_time, goaltime_sec, burden_weight, grade)

                if performance > max_performance:
                    max_performance = performance

            max_performance_list.append(max_performance)
    return max_performance_list
