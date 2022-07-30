import os
import sys
import logging
from datetime import date

# スクレイピング側とAI側で扱うパラメータを共通化するためのインタフェースとして機能する
# スクレイピングで取得するパラメータを変更する場合、ここをメンテすること
# pickleで保存できなくなるのでファイル読み書き系処理は追加しないこと

# debug initialize
# LEVEL : DEBUG < INFO < WARNING < ERROR < CRITICAL
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#logging.disable(logging.DEBUG)

class HorseDB:
    def __init__(self):
        self.horseID = []
        self.prof_contents = []
        self.blood_list = []
        self.perform_contents = []
        self.check = []

    def printAllMethodIndex(self, index):
        logger.info(self.horseID[index])
        logger.info(self.prof_contents[index])
        logger.info(self.blood_list[index])
        logger.info(self.perform_contents[index])
        logger.info(self.check[index])

    # 各パラメータセッタ
    def appendHorseID(self, data):
        self.horseID.append(data)
    
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
    