import os
import sys
import logging
from datetime import date
from dateutil.relativedelta import relativedelta

# スクレイピング側とAI側で扱うパラメータを共通化するためのインタフェースとして機能する
# スクレイピングで取得するパラメータを変更する場合、ここをメンテすること
# pickleで保存できなくなるのでファイル読み書き系処理は追加しないこと

# debug initialize
# LEVEL : DEBUG < INFO < WARNING < ERROR < CRITICAL
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#logging.disable(logging.DEBUG)

# ENUM horse_data
# horse_data = [horseID, prof_contents, blood_list, perform_contents, check]
# horseID = '1982101018'
# prof_contents = ['1982年4月22日', '00340', '辻幸雄', '谷岡正次', '静内町', '-', '1億330万円 (中央)', '15戦8勝 [8-3-1-3]', "86'札幌記念(G3)", 'ダンツウイッチ、フォースタテヤマ']
# blood_list = ['000a000b7f', '000a0009ab', '000a0035a9', '1975104765', '000a000416', '1955100859']
# perform_contents = [['1987/06/14', '198701010209', '13', '1', '1', '1.4', '1', '1', '00540', '59', '1:50.8', '-0.2', '1,600.0'], ['1986/12/07', '198607030611', '11', '6', '7', '1.5', '1', '1', '00540', '58', '2:19.7', '-0.4', '2,700.0'], ['1986/10/26', '198605040810', '16', '1', '2', '10.7', '3', '9', '00540', '58', '1:59.7', '1.4', ' '], ['1986/09/14', '198609040411', '7', '2', '2', '1.7', '1', '2', '00540', '57', '1:59.7', '0.0', '1,200.0'], ['1986/07/20', '198601020610', '9', '3', '3', '1.2', '1', '1', '00540', '58.5', '1:50.3', '-0.5', '1,400.0'], ['1986/06/29', '198601010809', '8', '3', '3', '2.4', '2', '1', '00540', '55', '2:02.3', '-0.8', '2,700.0'], ['1986/05/11', '198608030811', '17', '6', '12', '9.2', '3', '3', '00540', '54', '2:04.5', '0.3', '730.0'], ['1986/03/30', '198609020411', '10', '2', '2', '17.3', '8', '10', '00588', '56', '2:03.9', '2.3', ' '], ['1985/01/13', '198508010511', '16', '4', '7', '5.4', '1', '1', '00540', '55', '1:37.5', ' ', '2,600.0'], ['1984/12/16', '198407030809', '13', '1', '1', '7.2', '3', '1', '00540', '54', '1:50.1', ' ', '1,200.0'], ['1984/12/08', '198409050305', '9', '1', '1', '2.3', '1', '1', '00540', '54', '1:11.8', ' ', '480.0'], ['1984/11/18', '198408050607', '9', '2', '2', '3.6', '1', '2', '00126', '54', '1:11.6', ' ', '190.0'], ['1984/10/27', '198408040710', '11', '6', '7', '13.6', '6', '9', '00126', '52', '1:37.6', ' ', ' '], ['1984/09/23', '198409040602', '7', '2', '2', '1.6', '1', '1', '00126', '53', '1:14.0', ' ', '440.0'], ['1984/09/09', '198409040206', '13', '3', '3', '10.1', '5', '2', '00126', '53', '1:24.9', ' ', '180.0']]
# ["日付", レース名id, "頭数", "枠番", "馬番", "オッズ", "人気", "着順", 騎手id, "斤量", "タイム", "着差", "賞金"]
# check = 1 
# 欠落データ 1 : 無し, 0 : 有り

class HorseDB:
    def __init__(self):
        self.horseID = []
        self.common = []
        self.prof_contents = []
        self.blood_list = []
        self.perform_contents = []
        self.check = []

    # 一貫性チェック
    # すべての要素の数は同じである必要がある
    def selfConsistencyCheck(self):
        lengthMtr = len(self.horseID)
        errMsg  = "CHECK HorseDB CONSISTENCY !! => (len(horseID) != len({0})) == ({1} != {2})"
        consisFlg = True

        lengthSlv = len(self.common)
        if lengthMtr != lengthSlv:
            logger.critical(errMsg.format("common", lengthMtr, lengthSlv))
            consisFlg = False

        lengthSlv = len(self.prof_contents)
        if lengthMtr != lengthSlv:
            logger.critical(errMsg.format("prof_contents", lengthMtr, lengthSlv))
            consisFlg = False

        lengthSlv = len(self.blood_list)
        if lengthMtr != lengthSlv:
            logger.critical(errMsg.format("blood_list", lengthMtr, lengthSlv))
            consisFlg = False

        lengthSlv = len(self.perform_contents)
        if lengthMtr != lengthSlv:
            logger.critical(errMsg.format("perform_contents", lengthMtr, lengthSlv))
            consisFlg = False

        lengthSlv = len(self.check)
        if lengthMtr != lengthSlv:
            logger.critical(errMsg.format("check", lengthMtr, lengthSlv))
            consisFlg = False
        
        logger.info("Self consistency check : PASS (length = {})".format(lengthMtr))
        return consisFlg

    # checkが0の箇所を再確認し，修正可能なら修正する
    def reconfirmCheck(self):
        # checkが0の馬のindexを抽出
        need_reconfirm_idx = []
        for i in range(len(self.check)):
            if self.check[i] == 0:
                need_reconfirm_idx.append(i)
        logger.info("{} horses need be reconfirmed.".format(len(self.check)-len(need_reconfirm_idx)))
        logger.info("indices:")
        logger.info(need_reconfirm_idx)

        # 修正処理
        idx_list = []
        for idx in need_reconfirm_idx:
            new_perform_contents = []
            perform = self.perform_contents[idx]
            for race_row in perform:
                if race_row[7] == "除": #着順が"除"のレースを除外 (競走除外)
                    continue
                if race_row[7] == "取": #着順が"取"のレースを除外 (出生取消)
                    continue
                if race_row[7] == "": #着順が存在しないレースを除外 (開催延期?)
                    continue
                new_perform_contents.append(race_row)
            self.perform_contents[idx] = new_perform_contents

            race_prof = int(self.prof_contents[idx][-3][:self.prof_contents[idx][-3].find("戦")])
            race_perform = len(new_perform_contents)
            if race_prof == race_perform:
                self.check[idx] = 1
            
            if race_prof > race_perform: #競走成績に記録されていないレースがある馬 (未解決)
                idx_list.append(idx)
        if idx_list != []:
            logger.info("(prof > perform) indices:")
            logger.info(idx_list)
        logger.info("reconfirming end")

        # 再度checkが0の馬の数を集計
        count = 0
        for i in range(len(self.check)):
            if self.check[i] == 0:
                count += 1
        logger.info("{} horses remain.".format(count))
        logger.debug("reconfimCheck comp")

    def printAllMethodIndex(self, index):
        logger.info("horseID => ")
        logger.info(self.horseID[index])
        logger.info("common => ")
        logger.info(self.common[index])
        logger.info("prof_contents => ")
        logger.info(self.prof_contents[index])
        logger.info("blood_list => ")
        logger.info(self.blood_list[index])
        logger.info("perform_contents => ")
        logger.info(self.perform_contents[index])
        logger.info("check => ")
        logger.info(self.check[index])

    # 各パラメータセッタ
    def appendHorseID(self, data):
        self.horseID.append(data)

    def appendCommon(self, data):
        self.common.append(data)
    
    def appendProfContents(self, data):
        self.prof_contents.append(data)

    def appendBloodList(self, data):
        self.blood_list.append(data)
    
    def appendPerformContents(self, data):
        self.perform_contents.append(data)
    
    def appendCheck(self, data):
        self.check.append(data)

    def getHorseInfo(self, searchID):
        for index in range(len(self.horseID)):
            if self.horseID[index] == searchID:
                return index

    def getBirthDay(self, index):
        # 誕生日を取り出す
        # 以下の前提で計算する
        # prof_contents[index][0] に誕生日が含まれていること
        data = self.prof_contents[index][0]
        birthYear = int(data.split("年")[0])
        birthMon = int(data.split("年")[1].split("月")[0])
        birthDay = int(data.split("月")[1].split("日")[0])
        return date(birthYear, birthMon, birthDay)

    def ageConv2Day(self, birthday, raceday):
        # レース開催日の馬の年齢を計算
        # 小数点以下閏年未考慮
        dy = relativedelta(birthday, raceday)
        age = dy.years + (dy.months / 12.0) + (dy.days / 365.0)
        return age
    
    def getJockeyID(self, index, raceID):
        # index馬の出場したレース一覧からraceIDの一致した時の騎手IDを返す
        # 以下の前提で計算する
        # perform_contents[1] が raceID であること
        # perform_contents[8] が 騎手ID であること
        # perform_contents = [['1987/06/14', '198701010209', '13', '1', '1', '1.4', '1', '1', '00540', '59', '1:50.8', '-0.2', '1,600.0'], ['1986/12/07', '198607030611', '11', '6', '7', '1.5', '1', '1', '00540', '58', '2:19.7', '-0.4', '2,700.0'], ['1986/10/26', '198605040810', '16', '1', '2', '10.7', '3', '9', '00540', '58', '1:59.7', '1.4', ' '], ['1986/09/14', '198609040411', '7', '2', '2', '1.7', '1', '2', '00540', '57', '1:59.7', '0.0', '1,200.0'], ['1986/07/20', '198601020610', '9', '3', '3', '1.2', '1', '1', '00540', '58.5', '1:50.3', '-0.5', '1,400.0'], ['1986/06/29', '198601010809', '8', '3', '3', '2.4', '2', '1', '00540', '55', '2:02.3', '-0.8', '2,700.0'], ['1986/05/11', '198608030811', '17', '6', '12', '9.2', '3', '3', '00540', '54', '2:04.5', '0.3', '730.0'], ['1986/03/30', '198609020411', '10', '2', '2', '17.3', '8', '10', '00588', '56', '2:03.9', '2.3', ' '], ['1985/01/13', '198508010511', '16', '4', '7', '5.4', '1', '1', '00540', '55', '1:37.5', ' ', '2,600.0'], ['1984/12/16', '198407030809', '13', '1', '1', '7.2', '3', '1', '00540', '54', '1:50.1', ' ', '1,200.0'], ['1984/12/08', '198409050305', '9', '1', '1', '2.3', '1', '1', '00540', '54', '1:11.8', ' ', '480.0'], ['1984/11/18', '198408050607', '9', '2', '2', '3.6', '1', '2', '00126', '54', '1:11.6', ' ', '190.0'], ['1984/10/27', '198408040710', '11', '6', '7', '13.6', '6', '9', '00126', '52', '1:37.6', ' ', ' '], ['1984/09/23', '198409040602', '7', '2', '2', '1.6', '1', '1', '00126', '53', '1:14.0', ' ', '440.0'], ['1984/09/09', '198409040206', '13', '3', '3', '10.1', '5', '2', '00126', '53', '1:24.9', ' ', '180.0']]
        for races in self.perform_contents[index]:
            if races[1] == raceID:
                return races[8]
        # 見つからない場合
        return "-1"

    def countJockeyAppear(self, jockeyID):
        # jockey累計出走回数
        count = 0
        if jockeyID != "-1":
            for i in self.perform_contents:
                for j in i:
                    if j[8] == jockeyID:
                        count += 1
        return count
    
    def enumAllJockeyID(self):
        # jockeyIDのlistを返す．ただし，名前のままも存在する．
        id_set = set()
        for horse_perform in self.perform_contents:
            for race_perform in horse_perform:
                id_set.add(race_perform[8])
        return list(id_set)

    def getTotalEarned(self, index):
        # 生涯獲得賞金
        total = 0
        for content in self.perform_contents[index]:
            money = float(content[-1].replace(",",""))
            total += money
        return total

    def getTotalWLRatio(self, index):
        wl = []
        # '24戦4勝 [4-1-2-17]'
        match = self.prof_contents[index][7]
        # 4-1-2-17]
        match = match.split("[")[1]
        wl.append(float(match.split("-")[0])) # 1st
        wl.append(float(match.split("-")[1])) # 2nd
        wl.append(float(match.split("-")[2])) # 3rd
        return wl

    def getBurdenWeight(self, horseidx, raceid):
        # horseidx が raceid に出馬した時の斤量を返す
        # 見つからなかった場合、60[kg]とする
        for i in self.perform_contents[horseidx]:
            if i[1] == raceid:
                return float(i[9])
        return float(60)

    def getPostPosition(self, horseidx, raceid):
        # horseidx が raceid に出馬した時の枠番を返す
        # 見つからなかった場合、6枠とする
        for i in self.perform_contents[horseidx]:
            if i[1] == raceid:
                return float(i[3])
        return float(6)
