# エンコーダの追加方法
# 1. エンコーダクラスを以下のテンプレートから作成する
# 2. __init__.py に1.で作成したクラス追加
# 3. 推測時の入力用クラスを predictClass.py に追記する(正解ラベル用なら不要)
# 4. table.py のメンテナンス
# 4.1. XTbl に1.で作成したクラス追加
# 4.2. predict_XTbl に2.で作成したクラスを追加しておく
# 5. ログの整理, __main__ エントリーポイントの削除
# 6. 完

from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from Encoder_X import XClass

class XXXClass(XClass):

    def get(self):
        # DB データ問い合わせを行う
        # 問い合わせ関数は NetkeibaDB_IF.py に追記して呼び出して下さい
        # !! 推測時にも入力できるデータのみをここで取得すること
        # エンコード対象の race_id は XClass の self.race_id に格納してから実行してください
        # 出走する馬一覧取得
        # horse_id_list = self.nf.db_race_list_horse_id(self.race_id)
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
    from NetkeibaDB_IF import NetkeibaDB_IF
    from selfcheck import selfcheck
    from iteration_utilities import deepflatten

    # コンソール表示上、有効桁数は2桁とする
    np.set_printoptions(precision=2, linewidth=150)

    # エンコーダをテストする関数
    test = XXXClass()

    # テストに使うrace_id
    nf = NetkeibaDB_IF("RAM", read_only=True)
    race_id_list = nf.db_race_list_id(1800, 2023, -1, False)
    
    result_list = []
    # エンコード結果は固定長である必要があるので確認
    before_len = 0
    for race_id in race_id_list:
        # レースIDセット
        test.set(race_id)
        # エンコード実行
        test.adj()
        # 要素数チェック
        if ((before_len != len(test.xList)) and (before_len != 0)):
            logger.critical("CHECK ARRAY SIZE !! before = {0}, after = {1}".format(before_len, len(test.xList)))
        before_len = len(test.xList)
        # 結果確認
        logger.info("race_id = {0} | result = {1}".format(race_id, np.array(test.xList)))
        result_list.append(list(deepflatten(test.xList)))
    
    # 結果の妥当性を確認する
    # 最大値 or 最小値が nan になった場合、
    # 標準化の過程でゼロ除算などを行った可能性がある。
    # そのまま学習すると勾配が無限大に発散してしまうため、要修正
    selfcheck("XXXClass", result_list)
