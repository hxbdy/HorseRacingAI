# AI に入力するための標準化までを行うクラス

import numpy as np
import re
import copy
import time

from multiprocessing import Process, Queue
from dateutil.relativedelta import relativedelta

from debug import *
from getFromDB import * # db ハンドラはここで定義済み

class XClass:
    # 全インスタンス共通の変数
    race_id = '0'

    pad_size = 18

    def __init__(self):
        self.xList = []
        
    def set(self, target_race_id):
        XClass.race_id = target_race_id

    def get(self):
        if XClass.race_id == '0':
            logger.critical("race_id == 0 !!")

    def fix(self):
        None

    def pad(self):
        None

    def nrm(self):
        None

    def adj(self):
        # 各関数で self.xList を更新する
        self.get()
        self.fix()
        self.pad()
        self.nrm()
        return self.xList

class MoneyClass(XClass):
    def __init__(self):
        super().__init__()

    def set(self, race_id):
        super().set(race_id)

    def get(self):
        self.xList = db_race_list_prize(self.race_id)
    
    def fix(self):
        # 賞金リストをfloat変換する
        rowList = self.xList
        moneyList = []
        for m in rowList:
            if m == "":
                fm = "0.0"
            else:
                fm = m.replace(",","")
            moneyList.append(float(fm))
        self.xList = moneyList

    def pad(self):
        adj_size = abs(XClass.pad_size - len(self.xList))

        # ダミーデータ：0
        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            for i in range(adj_size):
                self.xList.append(0)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        # 賞金標準化
        # 1位賞金で割る
        # moneyList は float前提
        money1st = self.xList[0]
        moneyNrmList = []
        for m in self.xList:
            moneyNrmList.append(m / money1st)
        self.xList = moneyNrmList

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class HorseNumClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        self.xList = db_race_num_horse(self.race_id)
        
    def fix(self):
        XClass.fix(self)

    def pad(self):
        XClass.pad(self)

    def nrm(self):
        # 最大出走馬数で割って標準化
        self.xList = [float(self.xList[0]) / XClass.pad_size]

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class CourseConditionClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        raceData1List = db_race_list_race_data1(self.race_id)
        # コース状態取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = raceData1List[0].split(":")[2]
        #  良 / 発走 
        sep1 = sep1.split("/")[0]
        # 良
        sep1 = sep1.replace(" ", "")

        self.xList = sep1

    def fix(self):
        # 馬場状態のone-hot表現(ただし良は全て0として表現する)
        condition_dict = {'良':-1, '稍重':0, '重':1, '不良':2, '良ダート':3, '稍重ダート':4, '重ダート':5, '不良ダート':6}
        condition_onehot = [0] * len(condition_dict)
        hot_idx = condition_dict[self.xList]
        if hot_idx != -1:
            condition_onehot[hot_idx] = 1
        self.xList = condition_onehot

    def pad(self):
        XClass.pad(self)

    def nrm(self):
        XClass.nrm(self)

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class CourseDistanceClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        raceData1List = db_race_list_race_data1(self.race_id)
        # 距離取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = raceData1List[0].split(":")[0]
        # 芝右1600m
        # 数字以外を削除
        sep1 = re.sub(r'\D', '', sep1)
        sep1 = sep1.replace(" ", "")
        # 他と統一するためリストにする
        self.xList = [float(sep1)]

    def fix(self):
        XClass.fix(self)

    def pad(self):
        XClass.pad(self)

    def nrm(self):
        # 最長距離で割って標準化
        MAX_DISTANCE = 3600.0
        npcdList = np.array(self.xList)
        npcdList = npcdList / MAX_DISTANCE
        self.xList = npcdList.tolist()

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class RaceStartTimeClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        raceData1List = db_race_list_race_data1(self.race_id)
        # 出走時刻取得
        # race_data1 => 芝右1600m / 天候 : 晴 / 芝 : 良 / 発走 : 15:35
        sep1 = raceData1List[0].split("/")[3]
        #  発走 : 15:35
        sep1 = sep1.split(" : ")[1]
        #  15:35
        sep1 = sep1.replace(" ", "")

        self.xList = sep1

    def fix(self):
        # 発走時刻の数値化(時*60 + 分)
        t = self.xList.split(":")
        min = float(t[0])*60 + float(t[1])
        self.xList = [min]

    def pad(self):
        XClass.pad(self)

    def nrm(self):
        # 遅い時間ほど馬場が荒れていることを表現する
        # 最終出走時間 16:30 = 16 * 60 + 30 = 990 で割る
        self.xList = [self.xList[0] / 990]

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class WeatherClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        raceData1List = db_race_list_race_data1(self.race_id)
        sep1 = raceData1List[0].split(":")[1]
        #  晴 / 芝 
        sep1 = sep1.split("/")[0]
        # 晴 
        sep1 = sep1.replace(" ", "")
        self.xList = sep1

    def fix(self):
        # 天気のone-hot表現(ただし晴は全て0として表現する)
        # 出現する天気は6種類
        weather_dict = {'晴':-1, '曇':0, '小雨':1, '雨':2, '小雪':3, '雪':4}
        weather_onehot = [0] * 5
        hot_idx = weather_dict[self.xList]
        if hot_idx != -1:
            weather_onehot[hot_idx] = 1
        self.xList = weather_onehot

    def pad(self):
        XClass.pad(self)

    def nrm(self):
        XClass.nrm(self)

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class HorseAgeClass(XClass):
    def __init__(self):
        super().__init__()
        self.d0 = 0
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        if self.race_id == '0':
            logger.critical("ERROR : SET race_id")
        else:
            # 出走馬の誕生日リストを作成
            horseList = db_race_list_horse_id(self.race_id)
            bdList = []
            for horse_id in horseList:
                bod = db_horse_bod(horse_id)
                bdList.append(bod)
            self.xList = bdList
            # レース開催日を取得
            self.d0 = db_race_date(self.race_id)

    def fix(self):
        if self.d0 == 0:
            logger.critical("ERROR : SET d0")
        # 標準化の前に誕生日を日数表記にしておく
        bdList = self.xList
        for i in range(len(bdList)):
            dy = relativedelta(self.d0, bdList[i])
            age = dy.years + (dy.months / 12.0) + (dy.days / 365.0)
            bdList[i] = age
        self.xList = bdList

    def pad(self):
        # 年齢リスト拡張
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            # ダミーデータ：平均値
            mean_age = np.mean(self.xList)
            for i in range(adj_size):
                self.xList.append(mean_age)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        # 馬年齢標準化
        # 若いほうが強いのか, 年季があるほうが強いのか...
        # 最高値ですべてを割る
        nHorseAgeList = np.array(self.xList)
        maxAge = np.max(nHorseAgeList)
        nHorseAgeList = nHorseAgeList / maxAge
        self.xList = nHorseAgeList.tolist()

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class BurdenWeightClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        burdenWeightList = db_race_list_burden_weight(self.race_id)
        self.xList = burdenWeightList

    def fix(self):
        XClass.fix(self)

    def pad(self):
        # 斤量リスト拡張
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            # ダミーデータ：平均値
            mean_age = np.mean(self.xList)
            for i in range(adj_size):
                self.xList.append(mean_age)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        # 斤量の標準化
        # 一律60で割る
        SCALE_PARAMETER = 60
        n_weight_list = np.array(self.xList)
        n_weight_list = n_weight_list / SCALE_PARAMETER
        self.xList = n_weight_list.tolist()

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class PostPositionClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        postPositionList = db_race_list_post_position(self.race_id)
        self.xList = postPositionList

    def fix(self):
        XClass.fix(self)

    def pad(self):
        # 枠番リスト拡張
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            # ダミーデータ：拡張サイズに達するまで，1から順に追加．
            for i in range(adj_size):
                self.xList.append(i%8+1)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        # 枠番標準化
        # sigmoidで標準化
        nPostPositionList = np.array(self.xList)
        nPostPositionList = 1/(1+np.exp(nPostPositionList))
        self.xList = nPostPositionList.tolist()

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class JockeyClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        jockeyIDList = db_race_list_jockey(self.race_id)
        self.xList = jockeyIDList

    def fix(self):
        # 騎手の総出場回数を求める
        jockeyIDList = self.xList
        for i in range(len(jockeyIDList)):
            cnt = db_race_cnt_jockey(jockeyIDList[i])
            jockeyIDList[i] = cnt
        self.xList = jockeyIDList

    def pad(self):
        # 騎手ダミーデータ挿入
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            # ダミーデータ：出場回数50を追加．
            for i in range(adj_size):
                self.xList.append(50)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        # 騎手標準化
        # 最高値ですべてを割る
        njockeyList = np.array(self.xList)
        maxJockey = np.max(njockeyList)
        njockeyList = njockeyList / maxJockey
        self.xList = njockeyList.tolist()

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class UmamusumeClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        # 出馬リストを取得
        horse_list = db_race_list_horse_id(self.race_id)
        self.xList = horse_list

    def fix(self):
        # ウマ娘ちゃんテーブル
        umamusumeTbl = [
            "1995103211", #スペシャルウィーク
            "1994103997", #サイレンススズカ
            "1988101025", #トウカイテイオー
            "000a0003bd", #マルゼンスキー
            "1992109618", #フジキセキ
            "1985102167", #オグリキャップ
            "2009102739", #ゴールドシップ
            "2004104258", #ウオッカ
            "2004103198", #ダイワスカーレット
            "1994109686", #タイキシャトル
            "1995108676", #グラスワンダー
            "1991109852", #ヒシアマゾン
            "1987107235", #メジロマックイーン
            "1995108742", #エルコンドルパサー
            "1996100292", #テイエムオペラオー
            "1991108889", #ナリタブライアン
            "1981107017", #シンボリルドルフ
            "1993109154", #エアグルーヴ
            "1997110025", #アグネスデジタル
            "1995107393", #セイウンスカイ
            "1984101673", #タマモクロス
            "1999110187", #ファインモーション
            "1990103355", #ビワハヤヒデ
            "1992102988", #マヤノトップガン
            "1998101554", #マンハッタンカフェ
            "1989103049", #ミホノブルボン
            "1987105368", #メジロライアン
            "1992110167", #ヒシアケボノ
            "1990103565", #ユキノビジン
            "1989107699", #ライスシャワー
            "1987100579", #アイネスフウジン
            "1998101516", #アグネスタキオン
            "1996107396", #アドマイヤベガ
            "1984106229", #イナリワン
            "1990102314", #ウイニングチケット
            "1997103398", #エアシャカール
            "2007102951", #エイシンフラッシュ
            "2007102807", #カレンチャン
            "2003107045", #カワカミプリンセス
            "1984105823", #ゴールドシチー
            "1989108341", #サクラバクシンオー
            "1994109364", #シーキングザパール
            "1993106964", #シンコウウインディ
            "2001104313", #スイープトウショウ
            "1985104409", #スーパークリーク
            "2005100097", #スマートファルコン
            "2000101517", #ゼンノロブロイ
            "2006103169", #トーセンジョーダン
            "2006102424", #ナカヤマフェスタ
            "1990102766", #ナリタタイシン
            "1989107262", #ニシノフラワー
            "1996106177", #ハルウララ
            "1985104122", #バンブーメモリー
            "1991109886", #ビコーペガサス
            "1992103687", #マーベラスサンデー
            "1994100530", #マチカネフクキタル
            "1980107022", #ミスターシービー
            "1996110113", #メイショウドトウ
            "1994108393", #メジロドーベル
            "1988104866", #ナイスネイチャ
            "1995104427", #キングヘイロー
            "1989103489", #マチカネタンホイザ
            "1987104784", #イクノディクタス
            "1987105372", #メジロパーマー
            "1987102798", #ダイタクヘリオス
            "1988106332", #ツインターボ
            "2013106101", #サトノダイヤモンド
            "2012102013", #キタサンブラック
            "1985100743", #サクラチヨノオー
            "1982103448", #シリウスシンボリ
            "1985103406", #メジロアルダン
            "1985104215", #ヤエノムテキ
            "1995108246", #ツルマルツヨシ
            "1994108411", #メジロブライト
            "2017100720", #デアリングタクト
            "1991103498", #サクラローレル
            "1996102442", #ナリタトップロード
            "1988101069", #ヤマニンゼファー
            "1999110099", #シンボリクリスエス
            "1999100226", #タニノギムレット
            "1987100260", #ダイイチルビー
            "2004103323", #アストンマーチャン
            "1988107943", #ケイエスミラクル
            "2010106548", #コパノリッキー
            "2009100921", #ホッコータルマエ
            "2006106794", #ワンダーアキュート
        ]

        # 親にウマ娘ちゃんがいるか確認
        # 居た場合 1 にする
        umamusume_family = [0] * len(umamusumeTbl)
        horse_list = self.xList
        for i in range(len(horse_list)):
            # horse_list[i] の親にウマ娘ちゃんがいたら umamusume_family[i] = 1 とする
            # 親を取得
            parent_list = db_horse_list_parent(horse_list[i])
            # 親1頭ずつ確認する
            for parent in parent_list:
                # ウマ娘ちゃんならフラグをセットする
                for j in range(len(umamusumeTbl)):
                    if parent == umamusumeTbl[j]:
                        umamusume_family[j] = 1
                        # logger.debug("parent has umamusume : {0}".format(umamusumeTbl[j]))
        self.xList = umamusume_family

    def pad(self):
        XClass.pad(self)

    def nrm(self):
        XClass.nrm(self)

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class CumPerformClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def getForCalcPerformInfo(self, horse_list):
        horse_info_list = []
        for horse in horse_list:
            race = db_horse_list_perform(horse)
            horse_info_list.append(race)
        self.xList = horse_info_list

    def get(self):
        # race_id に出場した馬のリストを取得
        # fixでパフォーマンスを計算する
        horse_list = db_race_list_horse_id(self.race_id)
        self.getForCalcPerformInfo(horse_list)

    def getStandardTime(self, distance, condition, track, location):
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

    def getPerformance(self, standard_time, goal_time, weight, grade):
        # 走破タイム・斤量などを考慮し，「強さ(performance)」を計算
        # 以下のeffectの値，計算式は適当
        weight_effect = 1+ (55 - weight)/1000
        grade_effect_dict = {'G1':1.14, 'G2':1.12, 'G3':1.10, 'OP':1.0, 'J.G1':1.0, 'J.G2':1.0, 'J.G3':1.0}
        perform = (10 + standard_time - goal_time*weight_effect) * grade_effect_dict[grade]
        return perform

    def fix(self):
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
        performance = 0

        # raw = [[(馬Aレースa情報), (馬Aレースb情報), ... ], [(馬Bレースc情報), (馬Bレースd情報), ...]]
        for race in self.xList:
            for horse_info in race:
                # horse_info = ('1982106916', '3小倉8', '1:12.7', '53', '良', '芝1200', '-1')
                # logger.debug("horse_info = {0}".format(horse_info))
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
                # condition が空なら良にしておく
                if condition == '':
                    condition = '良'
                # 競馬場を取得 '3小倉8' のような数字が入っていることがあるので数字を削除
                location = re.sub(r'[0-9]+', '', horse_info[VENUE])
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
                if grade == "1" or grade =="2" or grade=="3":
                    grade = "G" + grade
                else:
                    grade = "OP"

                # 計算不能な場合を除いてperformanceを計算
                if track != "E" and distance != "E":
                    standard_time = self.getStandardTime(distance, condition, track, location)
                    performance = self.getPerformance(standard_time, goaltime_sec, burden_weight, grade)

                if performance > max_performance:
                    max_performance = performance

            max_performance_list.append(max_performance)

        self.xList = max_performance_list

    def pad(self):
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            # ダミーデータ：0を追加．
            for i in range(adj_size):
                self.xList.append(0)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        # sigmoidで標準化
        nPerformList = np.array(self.xList)
        nPerformList = 1/(1+np.exp(nPerformList))
        self.xList = nPerformList.tolist()

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class MarginClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        marginList = db_race_list_margin(self.race_id)
        self.xList = marginList

    def fix(self):
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
        for i in range(len(self.xList)):
            margin = self.xList[i]
            # 'クビ+1/2' などの特殊な表記に対応する
            if '+' in margin:
                m = margin.split('+')
                time += marginDict[m[0]]
                time += marginDict[m[1]]
            else:
                time += marginDict[margin]
            retList.append(time)
        self.xList = retList

    def pad(self):
        # 着差リスト拡張

        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            # ダミーデータ：最下位にハナ差で連続してゴールすることにする
            HANA = 0.0125
            lastMargin = self.xList[-1]
            for i in range(adj_size):
                lastMargin += HANA
                self.xList.append(lastMargin)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        # 着差標準化
        x = np.array(self.xList)
        ny = 1/(1+np.exp(-x))
        y = ny.tolist()
        # リストを逆順にする。元のリストを破壊するため注意。
        # 戻り値はNoneであることも注意
        y.reverse()
        self.xList = y

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class BradleyTerryClass(XClass):
    # 対戦表を作り、そこから強さを推定する
    # 出馬のリストを作成 ex:10頭出るレースの場合
    # race_result[10][10]
    # 1v1の対戦結果を格納していく
    # horse[0-10]:
    #  a = horse[0] vs horse[1] の試合数
    #  b = aの勝利数
    #  race_result[0][1] = horse[1]との勝利数
    #  race_result[1][0] = horse[1]との敗北数
    #  ...
    # それぞれの勝利数、敗北数を埋めたテーブルから強さを算出する
    # 20回ほど繰り返して精度を上げる
    # 尤度初期値 1
    # ex : p[0] = (合計勝利数) / sum((race_result[0][1] + race_result[1][0]/(p[0] + p[1])) , ... )
    # 1. 出場する馬一覧の2Dテーブルを作る
    # 2. 指定の2頭が出たレース一覧を取得
    # 3. 2.のレース情報からそれぞれ何勝何敗かを求める
    # 4. 3.の情報で1.のテーブルを埋める
    # 5. それぞれの強さを算出する
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        self.xList = db_race_list_horse_id(self.race_id)
        self.col_num = len(self.xList)

    def getRankFromDB(self, race_id, horse_id):
        # race_id で horse_id は何位だったか取得
        val = db_race_rank(race_id, horse_id)
        if val.isdigit():
            rank = int(val)
        else:
            # '除'などが稀に入っているため、そのときはビリ扱いとする
            rank = self.col_num
        return rank

    def gen_wl_table(self):
        # 馬数x馬数の対戦表作成
        self.wl_table = [[-1 for j in range(self.col_num)] for i in range(self.col_num)]

        for y in range(self.col_num):
            horse_y = self.xList[y]
            start_x = y + 1
            for x in range(start_x, self.col_num):
                win = 0
                lose = 0
                horse_x = self.xList[x]
                races = db_race_list_1v1(horse_y, horse_x)
                for race in races:
                    # race で horse_x, y は何位だったか取得
                    rank_y = self.getRankFromDB(race, horse_y)
                    rank_x = self.getRankFromDB(race, horse_x)
                    # 勝敗
                    if rank_y < rank_x:
                        win += 1
                    else:
                        lose += 1
                self.wl_table[y][x] = win
                self.wl_table[x][y] = lose        

    def calcPower(self):
        self.gen_wl_table()
        self.p = [1 for i in range(self.col_num)]
        for i in range(20):
            self.calcFrac()
            self.p_div()

    def calcFrac(self):
        for y in range(self.col_num):
            w = 0 # 分子
            b = 0 # 分母
            for x in range(self.col_num):
                if self.wl_table[y][x] != -1:
                    w += self.wl_table[y][x]
                    if (self.p[y] + self.p[x]) == 0:
                        b = 0
                    else:
                        b += float((self.wl_table[y][x] + self.wl_table[x][y]) / (self.p[y] + self.p[x]))
            if(b == 0):
                self.p[y] = 0
            else:
                self.p[y] = float(w / b)

    def p_div(self):
        sum_p = sum(self.p)
        for i in range(self.col_num):
            if sum_p == 0:
                self.p[i] = 0
            else:
                self.p[i] /= sum_p

    def fix(self):
        self.calcPower()
        self.xList = self.p

    def pad(self):
        # リスト拡張
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            # ダミーデータ：0を追加．
            for i in range(adj_size):
                self.xList.append(0)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]
        
    def nrm(self):
        XClass.nrm(self)

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

class ParentBradleyTerryClass(BradleyTerryClass):
    def get(self):
        childList = db_race_list_horse_id(self.race_id)
        parentList = []
        for i in range(len(childList)):
            # 父のidを取得
            parent = db_horse_father(childList[i])
            parentList.append(parent)
        self.xList = parentList
        self.col_num = len(self.xList)

class RankOneHotClass(XClass):
    def __init__(self):
        super().__init__()
    
    def set(self, race_id):
        super().set(race_id)

    def get(self):
        # 馬番で昇順ソートされた順位を文字列で取得
        self.xList = db_race_list_rank(self.race_id)

    def fix(self):
        retList = []
        # 順位を int 変換する
        # 着順"取"のような数字以外は99位とする
        # ex: https://db.netkeiba.com/race/198608010111/
        for i in range(len(self.xList)):
            if self.xList[i].isdigit():
                retList.append(int(self.xList[i]))
            else:
                retList.append(99)
        self.xList = retList

    def pad(self):
        # リスト拡張
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            # ダミーデータ：99を追加．
            for i in range(adj_size):
                self.xList.append(99)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

            # 1位の馬がリストから無くなってしまった。
            # 残ってる馬の中で一番順位がよかった馬を正解とする
            if (1 in self.xList) == False:
                logger.error("1st place horse was deleted, https://db.netkeiba.com/race/{0}/".format(self.race_id))

    def nrm(self):
        # 最小値の順位を取得
        rank_min = min(self.xList)

        # 最高順位を1とする
        for i in range(len(self.xList)):
            if self.xList[i] == rank_min:
                self.xList[i] = 1
            else:
                self.xList[i] = 0

    def adj(self):
        self.xList = XClass.adj(self)
        return self.xList

# 学習用入力データX, 教師データt を管理する
class MgrClass:
    def __init__(self, start_year, end_year, XclassTbl, tclassTbl, limit = -1):

        # 参照渡しのためディープコピーしておく
        self.XclassTbl = copy.copy(XclassTbl)
        self.tclassTbl = copy.copy(tclassTbl)

        # (start_year <= 取得範囲 <=  end_year) の race_id, レース数保持
        self.totalRaceList = db_race_list_id(start_year, end_year, limit)
        self.totalRaceNum  = len(self.totalRaceList)

        # 全標準化結果保持リスト
        self.totalXList = [[0 for j in range(len(self.XclassTbl))] for i in range(self.totalRaceNum)]
        self.totaltList = []

    def set_totalList(self, totalXList, totaltList):
        self.totalXList = totalXList
        self.totaltList = totaltList

    # 既存の標準化済みデータに新規に追加する
    def getAppendTotalList(self, append_x):

        # 追加クラス以外をNoneにする
        for i in range(len(self.XclassTbl)):
            self.XclassTbl[i] = None
        self.XclassTbl.append(append_x)

        # 追加クラス分の列をアペンド
        for i in range(len(self.totalXList)):
            self.totalXList[i].append(0)
        
        return self.getTotalList()

    # 既存の標準化済みデータから指定インデックスの要素を削除する
    def getRemoveTotalList(self, remove_x_idx):
        for i in range(len(self.XclassTbl)):
            self.XclassTbl[i] = None

        # 追加クラス分の列をアペンド
        for i in range(len(self.totalXList)):
            del self.totalXList[i][remove_x_idx]

        return self.getTotalList()

    # クラス名からXtblの何番目に入っているかを返す
    # TODO: もしかしてpython構文でカバーできる機能ではないか
    def get_idx_Xtbl(self, name):
        for idx in range(len(self.XclassTbl)):
            if self.XclassTbl[idx] != None:
                if self.XclassTbl[idx].__name__ == name:
                    return idx
        return -1

    def encoding(self, queue, encodeClass):
        # 結果保存リスト
        result_list = []
        # エンコード実行するクラスが学習データなのか教師データなのか区別する
        if encodeClass in self.XclassTbl:
            cat = "x"
        elif encodeClass in self.tclassTbl:
            cat = "t"
        else:
            cat = "unknown"

        # 進捗確認カウンタ
        comp_cnt = 1
        # エンコードクラス生成
        instance = encodeClass()
        for race in range(len(self.totalRaceList)):

            # エンコード進捗状況送信
            queue.put(["progress", cat, encodeClass.__name__, comp_cnt])
            comp_cnt += 1

            # DB 検索条件, 開催時点での各馬の年齢計算などに使用する
            # (マルチプロセス時、親XClassの変数は子クラス同士に影響しない)
            XClass.race_id = self.totalRaceList[race]

            # データ取得から標準化まで行う
            x_tmp = instance.adj()

            result_list.append(x_tmp)
        
        queue.put(["encoding", cat, encodeClass.__name__, result_list])

    def getTotalList(self):

        # エンコードデータ共有用キュー
        queue = Queue()

        # 処理時間計測開始
        time_sta = time.perf_counter()

        # マルチプロセス実行
        # TODO: logger はマルチプロセスに対応していないためログが乱れる
        #       ログ用プロセスを別途作成する必要がある
        encode_list =      copy.copy(self.XclassTbl)
        encode_list.extend(copy.copy(self.tclassTbl))
        for encode in encode_list:
            if encode == None:
                continue
            logger.info("encode {0} start".format(encode.__name__))
            process = Process(target = self.encoding, args = (queue, encode))
            process.start()

        # 全エンコード終了フラグ
        encoded_x_flg_list = [0] * len(self.XclassTbl)
        encoded_t_flg      = 0

        # エンコードをスキップする要素はあらかじめ完了フラグをセットしておく
        for i in range(len(encode_list)):
            if encode_list[i] == None:
                encoded_x_flg_list[i] = 1

        # 各エンコード状況, 結果受信
        while True:
            dequeue = queue.get()

            # 進捗確認用
            if dequeue[0] == "progress":
                if dequeue[1] == "x":
                    print("\r\033[{0}C[{1:4}]".format(self.get_idx_Xtbl(dequeue[2]) * 8, dequeue[3]), end="")
                elif dequeue[1] == "t":
                    print("\r\033[{0}C|[{1:4}]".format(len(self.XclassTbl) * 8, dequeue[3]), end="")
                else:
                    logger.critical("Undefined comm | category = progress | data = {0}".format(dequeue[1:]))

            # エンコード完了
            elif dequeue[0] == "encoding":
                if dequeue[1] == "x":
                    x = self.get_idx_Xtbl(dequeue[2])
                    # エンコード完了フラグセット
                    encoded_x_flg_list[x] = 1
                    # エンコード結果を格納
                    data = dequeue[3]
                    for y in range(self.totalRaceNum):
                        self.totalXList[y][x] = data[y]
                elif dequeue[1] == "t":
                    # エンコード完了フラグセット
                    encoded_t_flg = 1
                    # エンコード結果を格納
                    self.totaltList = dequeue[3]
                else:
                    logger.critical("Undefined comm | category = encoding | data = {0}".format(dequeue[1:]))

            # Unknown Comm
            else:
                logger.critical("Undefined comm | category = {0} | data = {1}".format(dequeue[0], dequeue[1:]))

            # 全エンコードが完了したかチェック
            if (0 in encoded_x_flg_list) or (encoded_t_flg == 0):
                continue
            else:
                break
        print()

        # 解析用情報取得
        analysis_train = []
        for i in range(len(self.totalRaceList)):
            odds = db_race_1st_odds(self.totalRaceList[i])
            grade = db_race_grade(self.totalRaceList[i])
            analysis_train.append([odds, grade])
            logger.info("analysis data get ... {0} / {1}".format(i, self.totalRaceNum))

        # 計測終了
        time_end = time.perf_counter()

        logger.info("========================================")
        logger.info("encoding time = {0} [sec]".format(time_end - time_sta))
        
        return self.totalXList, self.totaltList, analysis_train
