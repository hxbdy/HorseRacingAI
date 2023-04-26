

from Encoder_X import XClass

class WeatherClass(XClass):

    def get(self):
        raceData1List = self.nf.db_race_list_race_data1(self.race_id)
        sep1 = raceData1List[0].split(":")[1]
        #  晴 / 芝 
        sep1 = sep1.split("/")[0]
        # 晴 
        sep1 = sep1.replace(" ", "")
        self.xList = sep1

    def fix(self):
        ALGO = 1

        if ALGO == 1:
            # 天気のone-hot表現(ただし晴は全て0として表現する)
            # 出現する天気は6種類
            weather_dict = {'晴':-1, '曇':0, '小雨':1, '雨':2, '小雪':3, '雪':4}
            weather_onehot = [0] * len(weather_dict)
            hot_idx = weather_dict[self.xList]
            if hot_idx != -1:
                weather_onehot[hot_idx] = 1
            self.xList = weather_onehot
        elif ALGO == 2:
            # 天気のone-hot表現
            # 出現する天気は6種類
            weather_dict = {'晴':0, '曇':1, '小雨':2, '雨':3, '小雪':4, '雪':5}
            weather_onehot = [0] * len(weather_dict)
            hot_idx = weather_dict[self.xList]
            weather_onehot[hot_idx] = 1
            self.xList = weather_onehot

    def pad(self):
        pass
