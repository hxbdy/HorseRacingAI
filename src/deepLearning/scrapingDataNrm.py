import pickle
import sys
import os
import pathlib
import logging
import re
from datetime import date
from dateutil.relativedelta import relativedelta
import numpy as np
from iteration_utilities import deepflatten

# commonフォルダ内読み込みのため
deepLearning_dir = pathlib.Path(__file__).parent
src_dir = deepLearning_dir.parent
root_dir = src_dir.parent
dir_lst = [deepLearning_dir, src_dir, root_dir]
for dir_name in dir_lst:
    if str(dir_name) not in sys.path:
        sys.path.append(str(dir_name))

from common.RaceDB import RaceDB
from common.RaceGradeDB import RaceGradeDB

loc_list = ['札幌', '函館', '福島', '新潟', '東京', '中山', '中京', '京都', '阪神', '小倉']

## リストの指定サイズへの拡張
# 指定サイズより小さい場合に限りダミーデータを作成して，それらで埋める
# rowList : 拡張したいリスト
# listSize : 希望のリスト要素数
def padMoneyNrm(rowList, listSize):
    # 賞金リスト拡張
    # ダミーデータ：0
    exSize = listSize - len(rowList)
    if exSize > 0:
        for i in range(exSize):
            rowList.append(0)
    return rowList

def padGoalTimeNrm(rowList, listSize):
    # ゴールタイムリスト拡張
    # ダミーデータ：偏差値40程度のランダム値
    exSize   = listSize - len(rowList)
    if exSize > 0:
        nNrmList = np.array(rowList)
        sigma    = np.std(nNrmList)
        ave      = np.average(nNrmList)
        exRandList = np.random.uniform(-2*sigma, -sigma, exSize)
        exRandList += ave
        for ex in exRandList:
            rowList.append(ex)
    return rowList

def padMarginList(rowList, listSize):
    # 着差リスト拡張
    # ダミーデータ：最下位にハナ差で連続してゴールすることにする
    HANA = 0.0125
    exSize   = listSize - len(rowList)
    lastMargin = rowList[-1]
    if exSize > 0:
        for i in range(exSize):
            lastMargin += HANA
            rowList.append(lastMargin)
    return rowList

def padHorseAgeList(rowList, listSize):
    # 年齢リスト拡張
    # ダミーデータ：平均値
    mean_age = np.mean(rowList)
    exSize = listSize - len(rowList)
    if exSize > 0:
        for i in range(exSize):
            rowList.append(mean_age)
    return rowList

def padBurdenWeightList(rowList, listSize):
    # 斤量リスト拡張
    # ダミーデータ：平均値
    mean_weight = np.mean(rowList)
    exSize = listSize - len(rowList)
    if exSize > 0:
        for i in range(exSize):
            rowList.append(mean_weight)
    return rowList

def padPostPositionList(rowList, listSize):
    # 枠番リスト拡張
    # ダミーデータ：listSizeに達するまで，1から順に追加．
    exSize = listSize - len(rowList)
    if exSize > 0:
        for i in range(exSize):
            rowList.append(i%8+1)
    return rowList

def padJockeyList(rowList, listSize):
    # 騎手ダミーデータ挿入
    # ダミーデータ：出場回数50を追加．
    exSize = listSize - len(rowList)
    if exSize > 0:
        for i in range(exSize):
            rowList.append(50)
    return rowList

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
    t = start_time_string.split(":")
    min = float(t[0])*60 + float(t[1])
    # 最終出走時間 16:30 = 16 * 60 + 30 = 990 で割る
    min /= 990 
    return min

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

## 馬の強さを計算
def getStandardTime(distance, condition, track, location):
    # レースコースの状態に依存する基準タイム(秒)を計算して返す
    # performancePredictionで予測した係数・定数を下の辞書の値に入れる．
    # loc_dictのOtherは中央競馬10か所以外の場合の値．10か所の平均値を取って作成する．
    dis_coef = 0.066433
    intercept = -9.6875
    cond_dict = {'良':-0.3145, '稍重':0.1566, '重':0.1802, '不良':-0.0223}
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

# 累計値の計算
def calCumPerformance(horsedb):
    # 各レースの結果から強さ(performance)を計算し，その最大値を記録していく
    # (外れ値を除くために，2番目の強さでもいいかもしれない．)
    rgdb = read_data("raceGradedb")

    horsedb.cum_perform = []
    for horse_idx in range(len(horsedb.perform_contents)):
        horse_perform = horsedb.perform_contents[horse_idx] 
        max_performance_list = []
        max_performance = -1000.0
        horse_perform.reverse()
        for race_idx in range(len(horse_perform)):
            race_result = horse_perform[race_idx]
            # ゴールタイムを取得
            goaltime = race_result[10]
            try:
                goaltime_sec = float(goaltime.split(':')[0])*60 + float(goaltime.split(':')[1])
            except:
                goaltime_sec = 240
            # 斤量を取得
            try:
                burden_weight = float(race_result[9])
            except:
                burden_weight = 40
            # 馬場状態と競馬場を取得
            condition = horsedb.getCourseCondition(horse_idx, race_result[2])
            location = horsedb.getCourseLocation(horse_idx, race_result[2])
            if location not in loc_list:
                location = "Other"
            # 芝かダートか
            if race_result[11][0] == "芝":
                track = "芝"
            elif race_result[11][0] == "ダ":
                track = "ダ"
            else:
                track = "E"
            # コースの距離
            dis_str = race_result[11]
            try:
                distance = float(re.sub(r'\D', '', dis_str).replace(" ", ""))
            except:
                distance = "E"
            # レースのグレード (G1,G2,G3,OP)
            # 日本の中央競馬以外のレースは全てOP扱いになる
            try:
                raceid = race_result[2]
                race_year = int(race_result[0][0:4])
                grade = "OP"
                for i in range(len(rgdb.raceID_list)):
                    if race_year != int(rgdb.raceID_list_year[i]):
                        continue
                    if raceid in rgdb.raceID_list[i]:
                        grade = "G" + rgdb.raceID_list_grade[i]
            except:
                grade = "E"
                

            # 計算不能な場合を除いてperformanceを計算
            if track != "E" and distance != "E" and grade != "E":
                standard_time = horsedb.getStandardTime(distance, condition, track, location)
                performance = horsedb.getPerformance(standard_time, goaltime_sec, burden_weight, grade)

            if performance > max_performance:
                max_performance = performance
            max_performance_list.append(max_performance)
        max_performance_list.reverse()
        horsedb.cum_perform.append(max_performance_list)

def calCumNumOfWin(horsedb):
    # 累計勝利数を計算
    horsedb.cum_num_wins = []
    for horse_perform in horsedb.perform_contents:
        cum_win_list = []
        cum_win = 0
        horse_perform.reverse()
        for race_result in horse_perform:
            if race_result[8] == '1':
                cum_win += 1
            cum_win_list.append(cum_win)
        cum_win_list.reverse()
        horsedb.cum_num_wins.append(cum_win_list)

def calCumMoney(horsedb):
    # 累計獲得賞金を計算
    horsedb.cum_money = []
    for horse_perform in horsedb.perform_contents:
        cum_money_list = []
        cum_money = 0.0
        horse_perform.reverse()
        for race_result in horse_perform:
            if race_result[15] == ' ':
                money = 0.0
            else:
                money = float(race_result[15].replace(",",""))
            cum_money += money
            cum_money_list.append(cum_money)
        cum_money_list.reverse()
        horsedb.cum_money.append(cum_money_list)


OUTPUT_PATH = str(root_dir) + "\\dst\\learningList\\"

"""pickleでデータを読み込み・保存"""
def read_data(read_file_name):
    """
    learningListフォルダ内にpicle化したファイルを読み込む。
    存在しない場合は文字列を返す．
    """
    try:
        with open(OUTPUT_PATH + read_file_name + ".pickle", "rb") as f:
            data = pickle.load(f)
    except FileNotFoundError:
        data = "FileNotFoundError"
    return data

def save_data(save_data, save_file_name):
    """
    learningListフォルダ内にpicle化したファイルを保存する。
    """
    with open(OUTPUT_PATH + save_file_name + ".pickle", 'wb') as f:
        pickle.dump(save_data, f)

# if __name__ == "__main__":
#     # debug initialize
#     # LEVEL : DEBUG < INFO < WARNING < ERROR < CRITICAL
#     logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s [%(levelname)s] %(message)s')
#     logger = logging.getLogger(__name__)
#     logger.setLevel(logging.DEBUG)
#     logging.disable(logging.DEBUG)

#     # pickle読み込み
#     logger.info("Database loading")

#     # レース情報読み込み
#     with open(str(root_dir) + "\\dst\\scrapingResult\\racedb.pickle", 'rb') as f:
#             racedb = pickle.load(f)

#     # 馬情報読み込み
#     with open(str(root_dir) + "\\dst\\scrapingResult\\horsedb.pickle", 'rb') as f:
#             horsedb = pickle.load(f)

#     # G1-3情報読み込み
#     # with open(str(root_dir) + "\\dst\\scrapingResult\\raceGradedb.pickle", 'rb') as f:
#         #gradedb = pickle.load(f)

#     logger.info("Database loading complete")

#     # DBに一度のレースで出た馬の最大頭数を問い合わせる
#     maxHorseNum = racedb.getMaxHorseNumLargestEver()
    
#     totalXList = []
#     totaltList = []
#     totalRaceNum = len(racedb.raceID)

#     for race in range(len(racedb.raceID)):

#         logger.info("========================================")
#         logger.info("From RaceDB info =>")
#         logger.info("https://db.netkeiba.com/race/{0}".format(racedb.raceID[race]))
#         logger.info("Generating input data : {0}/{1}".format(race+1, totalRaceNum))

#         ## 正解ラベルの作成
#         """
#         # タイム取得
#         # 標準化 -> ダミーデータ挿入
#         goalTimeRowList = racedb.goalTimeConv2SecList(race)
#         goalTimeNrmList = nrmGoalTime(goalTimeRowList)
#         goalTimeExpList = padGoalTimeNrm(goalTimeNrmList, maxHorseNum)
#         racedbLearningList.append(nrmGoalTime(goalTimeExpList))
#         """
#         # 着差取得
#         # ダミーデータ挿入 -> 標準化
#         # これを教師データtとする
#         marginList = racedb.getMarginList(race)
#         marginExpList = padMarginList(marginList, maxHorseNum)
#         teachList = nrmMarginList(marginExpList)

#         ## 学習リスト作成 (レースデータ)
#         racedbLearningList = []

#         # 天気取得
#         # onehot表現 5列使用
#         # (わりとどうでもよい変数だと思うので，1変数に圧縮してもよいと思う)
#         for i in nrmWeather(racedb.getWeather(race)):
#             racedbLearningList.append(i)

#         # コース状態取得
#         # onehot表現 3列使用
#         # (1変数にしやすい変数であるが，onehotにして重みは学習に任せた方が良いと思う)
#         for i in nrmCourseCondition(racedb.getCourseCondition(race)):
#             racedbLearningList.append(i)

#         # 出走時刻取得
#         racedbLearningList.append(nrmRaceStartTime(racedb.getRaceStartTime(race)))

#         # 距離取得
#         # 最長距離で割って標準化
#         MAX_DISTANCE = 3600
#         distance = float(racedb.getCourseDistance(race))
#         racedbLearningList.append(distance / MAX_DISTANCE)

#         # 頭数取得
#         # 最大の出馬数で割って標準化
#         horseNum = float(racedb.getHorseNum(race))
#         racedbLearningList.append(horseNum / maxHorseNum)

#         # 賞金取得
#         # ダミーデータ挿入 -> 標準化
#         moneyList = racedb.getMoneyList(race)
#         moneyExpList = padMoneyNrm(moneyList, maxHorseNum)
#         racedbLearningList.append(nrmMoney(moneyExpList))

#         # 賞金取得 その2 : 全レースの最高金額で割って正規化
#         # ToDo : 最高金額を取得して割る作業を追加
#         #racedbLearningList.append(racedb.getMoneyList2(race))
        
#         logger.debug("[Weather, CourseCondition, RaceStartTime, CourseDistance, HorseNum, [Money]]")
#         logger.debug(racedbLearningList)

#         ## 学習リスト作成 (各馬のデータ)
#         # レース開催日取得
#         d0 = racedb.getRaceDate(race)

#         # === horsedb問い合わせ ===
#         horseAgeList = []
#         burdenWeightList = []
#         postPositionList = []
#         jockeyList = []
#         for horseID in racedb.horseIDs_race[race]:
#             logger.debug("========================================")
#             logger.debug("From HorseDB info =>")
            
#             # horsedb へ horseID の情報は何番目に格納しているかを問い合わせる
#             # 以降horsedbへの問い合わせは index を使う
#             index = horsedb.getHorseInfo(horseID)
#             logger.debug("https://db.netkeiba.com/horse/{0} => index : {1}".format(horseID, index))
            
#             # 生涯獲得金取得
#             # race時点での獲得賞金を取得
#             # horsedb.getTotalEarned(index)

#             # 通算成績取得[1st,2nd,3rd]
#             # race開催時点での獲得賞金を取得
#             # horsedb.getTotalWLRatio(index)

#             # 出走当時の年齢取得(d0 > d1)
#             d1 = horsedb.getBirthDay(index)
#             age = horsedb.ageConv2Day(d0, d1)
#             horseAgeList.append(age)

#             # 斤量取得
#             burdenWeight = horsedb.getBurdenWeight(index, racedb.raceID[race])
#             burdenWeightList.append(burdenWeight)

#             # 枠番取得
#             postPosition = horsedb.getPostPosition(index, racedb.raceID[race])
#             postPositionList.append(postPosition)

#             # 騎手取得
#             jockeyID = horsedb.getJockeyID(index, racedb.raceID[race])
#             cntJockey = horsedb.countJockeyAppear(jockeyID)
#             jockeyList.append(cntJockey)

#             logger.debug("[HorseAge, BurdenWeight, PostPosition, JockeyID]")
#             logger.debug("[{0}, {1}, {2}, {3}]".format(horseAgeList[-1], burdenWeightList[-1], postPositionList[-1], jockeyList[-1]))
        
#         # 各リストにダミーデータを挿入
#         logger.debug("========================================")
#         logger.debug("insert dummy data")
#         horseAgeList = padHorseAgeList(horseAgeList, maxHorseNum)
#         burdenWeightList = padBurdenWeightList(burdenWeightList, maxHorseNum)
#         postPositionList = padPostPositionList(postPositionList, maxHorseNum)
#         jockeyList = padJockeyList(jockeyList, maxHorseNum)
        
#         # 各リスト標準化
#         logger.debug("normalize X data")
#         horseAgeList = nrmHorseAge(horseAgeList)
#         burdenWeightList = nrmBurdenWeightAbs(burdenWeightList)
#         postPositionList = nrmPostPosition(postPositionList)
#         jockeyList = nrmJockeyID(jockeyList)

#         # 各リスト確認
#         logger.debug("========================================")
#         # 教師データt
#         logger.debug("t (len : {0})= {1}".format(len(teachList), teachList))
#         # 学習データX
#         logger.debug("racedbLearningList(len : {0}) = {1}".format(len(racedbLearningList), racedbLearningList))
#         logger.debug("horseAgeList(len : {0}) = {1}".format(len(horseAgeList), horseAgeList))
#         logger.debug("burdenWeightList(len : {0}) = {1}".format(len(burdenWeightList), burdenWeightList))
#         logger.debug("postPositionList(len : {0}) = {1}".format(len(postPositionList), postPositionList))
#         logger.debug("jockeyList(len : {0}) = {1}".format(len(jockeyList), jockeyList))

#         # 統合
#         learningList = [racedbLearningList, horseAgeList, burdenWeightList, postPositionList, jockeyList]
        
#         # 一次元化
#         learningList = list(deepflatten(learningList))

#         # 保存用リストに追加
#         totalXList.append(learningList)
#         totaltList.append(teachList)

#     # 書き込み
#     logger.info("========================================")
    
#     # 保存先フォルダの存在確認
#     os.makedirs(OUTPUT_PATH, exist_ok=True)

#     fn = "X"
#     logger.info("Save {0}{1}.pickle".format(OUTPUT_PATH, fn))
#     save_data(totalXList, fn)

#     fn = "t"
#     logger.info("Save {0}{1}.pickle".format(OUTPUT_PATH, fn))
#     save_data(totaltList, fn)
