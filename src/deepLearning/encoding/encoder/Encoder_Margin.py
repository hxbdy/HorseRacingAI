

import numpy as np

from Encoder_X import XClass

class MarginClass(XClass):

    def get(self):
        marginDict = self.nf.db_race_list_margin(self.race_id)
        self.xList = marginDict

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
        marginDict = {'同着':0, '':0, 'None':0, 'ハナ':0.0125, 'アタマ':0.025, 'クビ':0.05, '1/2':0.1, '3/4':0.15, '1':0.2, \
                      '1.1/4':0.2, '1.1/2':0.25, '1.3/4':0.3, '2':0.3, '2.1/2':0.4, '3':0.5, '3.1/2':0.6, '4':0.7, '5':0.9, \
                      '6':1.0, '7':1.2, '8':1.3, '9':1.5, '10':1.6, '大':1.7}
        time = 0
        horse_num_time_dict = {}
        for horse_num, margin in self.xList.items():
            # 'クビ+1/2' などの特殊な表記に対応する
            if '+' in margin:
                m = margin.split('+')
                time += marginDict[m[0]]
                time += marginDict[m[1]]
            else:
                if margin in marginDict.keys():
                    time += marginDict[margin]
                else:
                    pass
            horse_num_time_dict[horse_num] = time

        self.logger.debug(horse_num_time_dict)

        self.xList = sorted(horse_num_time_dict.items())
        self.xList = list(map(lambda x: x[1], self.xList))

        self.logger.debug(self.xList)

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
        # 最下位が0、1位が1になるような二次関数で評価する
        # y = - (1 / max^2)x^2 + 1
        x = np.array(self.xList)
        ny = -(1/(np.max(x)+0.001)**2) * x**2 + 1
        # 小数点以下4位まで
        ny = np.round(ny, 4)
        y = ny.tolist()
        # リストを逆順にする。元のリストを破壊するため注意。
        # 戻り値はNoneであることも注意
        # y.reverse()
        self.xList = y
