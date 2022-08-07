# スクレイピング側とAI側で扱うパラメータを共通化するためのインタフェースとして機能する
# スクレイピングで取得するパラメータを変更する場合、ここをメンテすること
# pickleで保存できなくなるのでファイル読み書き系処理は追加しないこと

class JockeyDB:
    def __init__(self):
        self.jockeyID = []
        self.jockey_name = []
        self.jockey_common = []
        self.jockey_year_result = []

    # 各パラメータセッタ
    def appendJockey(self, id, name, common, year_result_list):
        self.jockeyID.append(id)
        self.jockey_name.append(name)
        self.jockey_common.append(common)
        self.jockey_year_result.append(year_result_list)