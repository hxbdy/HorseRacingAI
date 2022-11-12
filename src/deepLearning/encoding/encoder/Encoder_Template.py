# エンコーダの追加方法
# 1. エンコーダクラスを以下のテンプレートから作成する
# 2. 推測時の入力用クラスを config_predict.py に追記する
# 3. __init__.py に1.で作成したクラス追加
# 4. table.py のメンテナンス
# 4.1. XTbl に1.で作成したクラス追加
# 4.2. chgXTbl にNoneを追加しておく
# 4.3. predict_XTbl に2.で作成したクラスを追加しておく
# 5. 完

from Encoder_X import XClass

import logging
logger = logging.getLogger("XXXClass")

class XXXClass(XClass):

    def get(self):
        # DB データ問い合わせを行う
        # 問い合わせ関数は getFromDB.py に追記して呼び出して下さい
        # self.xList = DB問い合わせ結果
        pass
    
    def fix(self):
        # 型変換などpadよりも前に行いたい処理はここで行う
        # self.xList = fixed self.xList
        pass

    def pad(self):
        # サイズの伸縮を行う
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            for i in range(adj_size):
                self.xList.append(0)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        # 標準化, 正規化を行う
        # 0-1の範囲に収めるのが好ましい
        # self.xList = normalized self.xList
        pass
