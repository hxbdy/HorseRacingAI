# エンコーダの追加方法
# 1. エンコーダクラスを以下のテンプレートから作成する
# 2. __init__.py に1.で作成したクラス追加
# 3. 推測時の入力用クラスを config_predict.py に追記する
# 4. table.py のメンテナンス
# 4.1. XTbl に1.で作成したクラス追加
# 4.2. chgXTbl にNoneを追加しておく
# 4.3. predict_XTbl に2.で作成したクラスを追加しておく
# 5. ログの整理, __main__ エントリーポイントの削除
# 6. 完

from Encoder_X import XClass
from debug import stream_hdl, file_hdl
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("XXXClass"))

class XXXClass(XClass):

    def get(self):
        # DB データ問い合わせを行う
        # 問い合わせ関数は getFromDB.py に追記して呼び出して下さい
        # !! 推測時にも入力できるデータのみをここで取得すること
        # self.xList = DB問い合わせ結果
        pass
    
    def fix(self):
        # 型変換などpadよりも前に行いたい処理はここで行う
        # self.xList = fixed self.xList
        pass

    def pad(self):
        # サイズの伸縮を行う
        # 固定値でパディングする場合はXClassのpad()を使おう.
        super().pad(0)

    def nrm(self):
        # 標準化, 正規化を行う
        # 0-1の範囲に収めるのが好ましい
        # self.xList = normalized self.xList
        pass

# 動作確認用
# このファイルを直接実行することで,このクラスのエンコードのみ動かせる
if __name__ == "__main__":
    import numpy as np
    from getFromDB import db_race_list_id
    from selfcheck import selfcheck

    # コンソール表示上、有効桁数は2桁とする
    np.set_printoptions(precision=2, linewidth=150)

    # エンコーダをテストする関数
    test = XXXClass()

    # テストに使うrace_id
    race_id_list = db_race_list_id(1800, 2020, -1)
    
    result_list = []
    for race_id in race_id_list:
        # レースIDセット
        test.set(race_id)
        # エンコード実行
        test.adj()
        # 結果確認
        logger.info("result = {0}".format(np.array(test.xList)))
        result_list.append(test.xList)
    
    # 結果の妥当性を確認する
    selfcheck(result_list)
