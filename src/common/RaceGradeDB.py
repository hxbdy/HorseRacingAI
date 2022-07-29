# スクレイピング側とAI側で扱うパラメータを共通化するためのインタフェースとして機能する
# スクレイピングで取得するパラメータを変更する場合、ここをメンテすること
# pickleで保存できなくなるのでファイル読み書き系処理は追加しないこと

class RaceGradeDB:
    def __init__(self):
        self.raceID_list = []
        self.raceID_list_year = []
        self.raceID_list_grade = []

    # 各パラメータセッタ
    def appendRaceIDList(self, raceID_list, year, grade):
        self.raceID_list.append(raceID_list)
        self.raceID_list_year.append(year)
        self.raceID_list_grade.append(grade)

    # raceID_listを1次元配列に直して出力
    def getRaceIDList(self):
        output = []
        for i in range(len(self.raceID_list)):
            output += self.raceID_list[i]
        return output
