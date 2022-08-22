import numpy as np

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

PadFuncTbl = {
    "padMoneyNrm"         : padMoneyNrm,
    "padGoalTimeNrm" : padGoalTimeNrm,
    "padMarginList" : padMarginList,
    "padHorseAgeList" : padHorseAgeList,
    "padBurdenWeightList" : padBurdenWeightList,
    "padPostPositionList" : padPostPositionList,
    "padJockeyList" : padJockeyList
}
