import os
import sys

# スクレイピング側とAI側で扱うパラメータを共通化するためのインタフェースとして機能する
# スクレイピングで取得するパラメータを変更する場合、ここをメンテすること
# pickleで保存できなくなるのでファイル読み書き系処理は追加しないこと

class HorseDB:
    def __init__(self):
        self.horseID = []
        self.prof_contents = []
        self.blood_list = []
        self.perform_contents = []
        self.check = []

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

    # 各パラメータゲッタ
    def getHorseID(self):
        return self.horseID

    def getProfContents(self):
        return self.prof_contents

    def getBloodList(self):
        return self.blood_list
    
    def getPerformContents(self):
        return self.perform_contents
    
    def getCheck(self):
        return self.check
