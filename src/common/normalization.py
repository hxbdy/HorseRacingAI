import numpy as np

## 値の標準化
def nrmWeather(weather_string):
    # 天気のone-hot表現(ただし晴は全て0として表現する)
    # 出現する天気は6種類
    weather_dict = {'晴':-1, '曇':0, '小雨':1, '雨':2, '小雪':3, '雪':4}
    weather_onehot = [0] * 5
    hot_idx = weather_dict[weather_string]
    if hot_idx != -1:
        weather_onehot[hot_idx] = 1
    
    return weather_onehot

def nrmCourseCondition(condition_string):
    # 馬場状態のone-hot表現(ただし良は全て0として表現する)
    condition_dict = {'良':-1, '稍重':0, '重':1, '不良':2}
    condition_onehot = [0] * 3
    hot_idx = condition_dict[condition_string]
    if hot_idx != -1:
        condition_onehot[hot_idx] = 1

    return condition_onehot

def nrmRaceStartTime(start_time_string):
    # 発走時刻の数値化(時*60 + 分)と標準化
    # 遅い時間ほど馬場が荒れていることを表現する
    minList = []
    for i in start_time_string:
        t = i.split(":")
        min = float(t[0])*60 + float(t[1])
        # 最終出走時間 16:30 = 16 * 60 + 30 = 990 で割る
        minList.append(min / 990 )
    return minList

def nrmHorseAge(horseAgeList):
    # 馬年齢標準化
    # 若いほうが強いのか, 年季があるほうが強いのか...
    # 最高値ですべてを割る
    nHorseAgeList = np.array(horseAgeList)
    maxAge = np.max(nHorseAgeList)
    nHorseAgeList = nHorseAgeList / maxAge
    return nHorseAgeList.tolist()

def nrmBurdenWeight(burdenWeightList):
    # 斤量標準化
    # 最高値ですべてを割る
    nburdenWeightList = np.array(burdenWeightList)
    maxBurdenWeight = np.max(nburdenWeightList)
    nburdenWeightList = nburdenWeightList / maxBurdenWeight
    return nburdenWeightList.tolist()

def nrmBurdenWeightAbs(weight_list):
    # 斤量の標準化
    # 一律60で割る
    SCALE_PARAMETER = 60
    n_weight_list = np.array(weight_list)
    n_weight_list = n_weight_list / SCALE_PARAMETER
    return n_weight_list.tolist()

def nrmPostPosition(postPositionList):
    # 枠番標準化
    # sigmoidで標準化
    nPostPositionList = np.array(postPositionList)
    nPostPositionList = 1/(1+np.exp(nPostPositionList))
    return nPostPositionList.tolist()

def nrmJockeyID(jockeyList):
    # 騎手標準化
    # 最高値ですべてを割る
    njockeyList = np.array(jockeyList)
    maxJockey = np.max(njockeyList)
    njockeyList = njockeyList / maxJockey
    return njockeyList.tolist()

def nrmGoalTime(goalTimeRowList):
    # ゴールタイム標準化
    # sigmoid で標準化．MUはハイパーパラメータ．
    # 計算式 : y = 1 / (1 + exp(x))
    # テキストではexp(-x)だが今回は値が小さい方が「良いタイム」のためexp(x)としてみた
    # 最大値 = 最下位のタイム
    npGoalTime = np.array(goalTimeRowList)

    ave = np.average(npGoalTime)
    MU = 50

    # ゴールタイム調整方法を選択
    METHOD = 3
    if METHOD == 1:
        y = 1 / (1 + np.exp(npGoalTime / ave))
    elif METHOD == 2:
        y = 1 / (1 + np.exp(npGoalTime / MU))
    elif METHOD == 3:
        y = 1 / (1 + np.exp((npGoalTime - ave) / MU))
    
    # ndarray と list の違いがよくわかっていないので一応リストに変換しておく
    return y.tolist()

def nrmMoney(moneyList):
    # 賞金標準化
    # 1位賞金で割る
    # moneyList は float前提
    money1st = moneyList[0]
    moneyNrmList = []
    for m in moneyList:
        moneyNrmList.append(m / money1st)
    return moneyNrmList

def nrmMarginList(marginList):
    # 着差標準化
    x = np.array(marginList)
    ny = 1/(1+np.exp(-x))
    y = ny.tolist()
    # リストを逆順にする。元のリストを破壊するため注意。
    # 戻り値はNoneであることも注意
    y.reverse()
    return y

def nrmCourseDistanceList(cdList):
    # 最長距離で割って標準化
    MAX_DISTANCE = 3600.0
    npcdList = np.array(cdList)
    npcdList = npcdList / MAX_DISTANCE
    return npcdList.tolist()

def nrmHorseNumList(hnList):
    # 最大出走馬数で割って標準化
    MAX_HORSE_NUM = 24.0
    npcdList = np.array(hnList)
    npcdList = npcdList / MAX_HORSE_NUM
    return npcdList.tolist()

def nrmCumPerformList(cpList):
    return cpList
    