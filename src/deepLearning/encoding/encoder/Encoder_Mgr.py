import copy
import time
import logging
from multiprocessing import Process, Queue

from debug     import stream_hdl, file_hdl
from Encoder_X import XClass
from NetkeibaDB_IF import NetkeibaDB_IF

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("output"))

class MgrClass:
    def __init__(self, start_year, end_year, XclassTbl, tclassTbl, limit = -1):

        # 参照渡しのためディープコピーしておく
        self.XclassTbl = copy.copy(XclassTbl)
        self.tclassTbl = copy.copy(tclassTbl)

        # (start_year <= 取得範囲 <=  end_year) の race_id, レース数保持
        nf = NetkeibaDB_IF("RAM")
        self.totalRaceList = nf.db_race_list_id(start_year, end_year, limit)
        self.totalRaceNum  = len(self.totalRaceList)

        # エンコード結果保持リスト
        self.totalXList = [[0 for j in range(len(self.XclassTbl))] for i in range(self.totalRaceNum)]
        self.totaltList = []

        # 全エンコード完了フラグ
        self.encode_comp_flg_x = [0] * len(self.XclassTbl)
        self.encode_comp_flg_t = 0

        # エンコードデータ共有用キュー
        self.queue = Queue()

    def setEncodeComplated(self, encoder, data):
        """エンコード完了フラグをセットする。エンコード結果をメンバに格納する"""
        if self.get_cat(encoder) == "x":
            idx = self.XclassTbl.index(encoder)
            self.encode_comp_flg_x[idx] = 1
            for y in range(self.totalRaceNum):
                self.totalXList[y][idx] = data[y]
        elif self.get_cat(encoder) == "t":
            self.encode_comp_flg_t = 1
            self.totaltList = data

    def isAllEncodeComplated(self):
        """全エンコードが終了したかを返す
        True: 全エンコード完了済み
        False: 未エンコードがある
        """
        if 0 in self.encode_comp_flg_x:
            return False
        if self.encode_comp_flg_t == 0:
            return False
        return True

    def print_progress(self, encoder, comp_cnt):
        """エンコードの進捗を出力する"""
        if self.get_cat(encoder) == "x":
            idx = self.XclassTbl.index(encoder)
            print("\r\033[{0}C[{1:4}]".format(idx * 8, comp_cnt), end="")
        elif self.get_cat(encoder) == "t":
            print("\r\033[{0}C|  [{1:4}]".format(len(self.XclassTbl) * 8, comp_cnt), end="")

    def get_cat(self, encoder) -> str:
        """エンコーダが学習用か、正解用か返す
        return x:学習用 t:正解用 unknown:どれにも該当しない(ありえないはず)
        """
        # エンコード実行するクラスが学習データなのか教師データなのか区別する
        if encoder in self.XclassTbl:
            cat = "x"
        elif encoder in self.tclassTbl:
            cat = "t"
        else:
            cat = "unknown"
        return cat

    def multiprocess_encode(self):
        """学習用、教師用のエンコーダをまとめてエンコードする"""
        encode_list =      copy.copy(self.XclassTbl)
        encode_list.extend(copy.copy(self.tclassTbl))
        for encode in encode_list:
            logger.info("encode {0} start".format(encode.__name__))
            process = Process(target = self.encoding, args = (encode, ))
            process.start()

    def encoding(self, encodeClass):
        # 結果保存リスト
        result_list = []

        # 進捗確認カウンタ
        comp_cnt = 1
        
        # エンコードクラス生成
        instance = encodeClass()
        for race in range(self.totalRaceNum):

            # エンコード進捗状況送信
            self.queue.put(["progress", encodeClass, comp_cnt])
            comp_cnt += 1

            # DB 検索条件, 開催時点での各馬の年齢計算などに使用する
            # (マルチプロセス時、親XClassの変数は子クラス同士に影響しない)
            XClass.race_id = self.totalRaceList[race]

            # データ取得から標準化まで行う
            x_tmp = instance.adj()

            result_list.append(x_tmp)
        
        self.queue.put(["encoding", encodeClass, result_list])

    def getTotalList(self):

        # 処理時間計測開始
        time_sta = time.perf_counter()

        # マルチプロセスエンコード実行
        self.multiprocess_encode()

        # 各エンコード状況, 結果受信
        while True:
            dequeue = self.queue.get()

            # 進捗確認用
            if dequeue[0] == "progress":
                self.print_progress(dequeue[1], dequeue[2])

            # エンコード完了
            elif dequeue[0] == "encoding":
                self.setEncodeComplated(dequeue[1], dequeue[2])

            # Unknown Comm
            else:
                logger.critical("Undefined comm | category = {0} | data = {1}".format(dequeue[0], dequeue[1:]))

            # 全エンコードが完了したかチェック
            if self.isAllEncodeComplated():
                break
            else:
                continue
        print()

        # 計測終了
        time_end = time.perf_counter()

        logger.info("========================================")
        logger.info("encoding time = {0} [sec]".format(time_end - time_sta))
        
        return self.totalXList, self.totaltList
