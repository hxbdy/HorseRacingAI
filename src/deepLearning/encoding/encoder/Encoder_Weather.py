import logging

from Encoder_X import XClass
from debug     import stream_hdl, file_hdl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("WeatherClass"))

class WeatherClass(XClass):

    def get(self):
        weather = self.nf.db_race_weather(self.race_id)
        self.xList = weather

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
