import TwoLayerNet
import numpy as np
import pickle
import sys
import pathlib
from iteration_utilities import deepflatten

# commonフォルダ内読み込みのため
deepLearning_dir = pathlib.Path(__file__).parent
src_dir = deepLearning_dir.parent
root_dir = src_dir.parent
dir_lst = [deepLearning_dir, src_dir, root_dir]
for dir_name in dir_lst:
    if str(dir_name) not in sys.path:
        sys.path.append(str(dir_name))

from common.getFromDB import *

# 保存済みパラメータ読み込み
net = TwoLayerNet.TowLayerNet(131,50,24)
net.loadParam()

# 推測するレース情報を入力
# 学習時でいう"get~()"で得られる結果と同じものを用意する

# 賞金
# [5400, 1000, 500]
moneyList = []

# 出走馬数
# [20]
horseNumList = []

# コース距離
# [1500]
courseDistanceList = []

# レース開始時刻
# ['15:30']
raceStartTimeList = []

# コース状態
# ['良']
courseConditionList = []

# 天気
# ['晴']
weatherList = []

# 馬の年齢
# レース開催日から計算するため、誕生日を入力する
horseAgeList = []

# 斤量
# [60, 50, 50]
burdenWeightList = []

# 枠番
# [1, 1, 2]
postPositionList = []

# 騎手
# 騎手IDを入力する
# [00123, 00124, 00125]
jockeyList = []

# パフォーマンス計算
# 出場する馬のパフォーマンスを計算するためまずはhorse_idをリスト化してから処理する
horse_list = []
cumPerformList = getParamForCalcPerform(horse_list)

# fix, pad, nrm

# flat
x = [
    moneyList,          
    horseNumList,       
    courseConditionList,
    courseDistanceList,
    raceStartTimeList,
    weatherList,
    horseAgeList,
    burdenWeightList,
    postPositionList,
    jockeyList,
    cumPerformList,
]
x = list(deepflatten(x))

# y = 各馬が1位になる確率
y = net.predict(x)
