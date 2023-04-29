from datetime import date

class RaceInfo():
    """レースデータを引き渡すための構造体
    """
    def __init__(self):
        self.date: date = date(1900, 1, 1)
        
        self.horse_num = 0
        self.race_id = ""

        self.start_time = ""
        self.distance = []
        self.weather = ""
        self.course_condition = ""
        self.prize = []

        self.post_position = []
        self.horse_number = []
        self.burden_weight = []
        self.horse_weight = []

        self.horse_id = []
        self.jockey_id = []

        # 推測結果
        # predictを実行することで結果が格納される
        self.predict_y = []

        # 自動で投票する時の投票先選択時に使用する
        # 推測時、エンコード時には使用しない
        self.venue = ""
        self.race_no = ""
