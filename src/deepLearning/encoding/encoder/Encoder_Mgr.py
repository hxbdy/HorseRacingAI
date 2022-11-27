import copy
import time

from multiprocessing import Process, Queue

from getFromDB import db_race_list_id, db_race_1st_odds, db_race_grade
from Encoder_X import XClass

from debug import stream_hdl, file_hdl

import logging

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
        self.totalRaceList = db_race_list_id(start_year, end_year, limit)
        self.totalRaceNum  = len(self.totalRaceList)

        # 全標準化結果保持リスト
        self.totalXList = [[0 for j in range(len(self.XclassTbl))] for i in range(self.totalRaceNum)]
        self.totaltList = []

    def set_totalList(self, totalXList, totaltList):
        self.totalXList = totalXList
        self.totaltList = totaltList

    # 既存の標準化済みデータに新規に追加する
    def getAppendTotalList(self, append_x):

        # 追加クラス以外をNoneにする
        for i in range(len(self.XclassTbl)):
            self.XclassTbl[i] = None
        self.XclassTbl.append(append_x)

        # 追加クラス分の列をアペンド
        for i in range(len(self.totalXList)):
            self.totalXList[i].append(0)
        
        return self.getTotalList()

    # 既存の標準化済みデータから指定インデックスの要素を削除する
    def getRemoveTotalList(self, remove_x_idx):
        for i in range(len(self.XclassTbl)):
            self.XclassTbl[i] = None

        # 追加クラス分の列をアペンド
        for i in range(len(self.totalXList)):
            del self.totalXList[i][remove_x_idx]

        return self.getTotalList()

    # クラス名からXtblの何番目に入っているかを返す
    # TODO: もしかしてpython構文でカバーできる機能ではないか
    def get_idx_Xtbl(self, name):
        for idx in range(len(self.XclassTbl)):
            if self.XclassTbl[idx] != None:
                if self.XclassTbl[idx].__name__ == name:
                    return idx
        return -1

    def encoding(self, queue, encodeClass):
        # 結果保存リスト
        result_list = []
        # エンコード実行するクラスが学習データなのか教師データなのか区別する
        if encodeClass in self.XclassTbl:
            cat = "x"
        elif encodeClass in self.tclassTbl:
            cat = "t"
        else:
            cat = "unknown"

        # 進捗確認カウンタ
        comp_cnt = 1
        # エンコードクラス生成
        instance = encodeClass()
        for race in range(len(self.totalRaceList)):

            # エンコード進捗状況送信
            queue.put(["progress", cat, encodeClass.__name__, comp_cnt])
            comp_cnt += 1

            # DB 検索条件, 開催時点での各馬の年齢計算などに使用する
            # (マルチプロセス時、親XClassの変数は子クラス同士に影響しない)
            XClass.race_id = self.totalRaceList[race]

            # データ取得から標準化まで行う
            x_tmp = instance.adj()

            result_list.append(x_tmp)
        
        queue.put(["encoding", cat, encodeClass.__name__, result_list])

    def getTotalList(self):

        # エンコードデータ共有用キュー
        queue = Queue()

        # 処理時間計測開始
        time_sta = time.perf_counter()

        # マルチプロセス実行
        encode_list =      copy.copy(self.XclassTbl)
        encode_list.extend(copy.copy(self.tclassTbl))
        for encode in encode_list:
            if encode == None:
                continue
            logger.info("encode {0} start".format(encode.__name__))
            process = Process(target = self.encoding, args = (queue, encode))
            process.start()

        # 全エンコード終了フラグ
        encoded_x_flg_list = [0] * len(self.XclassTbl)
        encoded_t_flg      = 0

        # エンコードをスキップする要素はあらかじめ完了フラグをセットしておく
        for i in range(len(encode_list)):
            if encode_list[i] == None:
                encoded_x_flg_list[i] = 1

        # 各エンコード状況, 結果受信
        while True:
            dequeue = queue.get()

            # 進捗確認用
            if dequeue[0] == "progress":
                if dequeue[1] == "x":
                    print("\r\033[{0}C[{1:4}]".format(self.get_idx_Xtbl(dequeue[2]) * 8, dequeue[3]), end="")
                elif dequeue[1] == "t":
                    print("\r\033[{0}C|  [{1:4}]".format(len(self.XclassTbl) * 8, dequeue[3]), end="")
                else:
                    logger.critical("Undefined comm | category = progress | data = {0}".format(dequeue[1:]))

            # エンコード完了
            elif dequeue[0] == "encoding":
                if dequeue[1] == "x":
                    x = self.get_idx_Xtbl(dequeue[2])
                    # エンコード完了フラグセット
                    encoded_x_flg_list[x] = 1
                    # エンコード結果を格納
                    data = dequeue[3]
                    for y in range(self.totalRaceNum):
                        self.totalXList[y][x] = data[y]
                elif dequeue[1] == "t":
                    # エンコード完了フラグセット
                    encoded_t_flg = 1
                    # エンコード結果を格納
                    self.totaltList = dequeue[3]
                else:
                    logger.critical("Undefined comm | category = encoding | data = {0}".format(dequeue[1:]))

            # Unknown Comm
            else:
                logger.critical("Undefined comm | category = {0} | data = {1}".format(dequeue[0], dequeue[1:]))

            # 全エンコードが完了したかチェック
            if (0 in encoded_x_flg_list) or (encoded_t_flg == 0):
                continue
            else:
                break
        print()

        # 解析用情報取得
        analysis_train = []
        for i in range(len(self.totalRaceList)):
            odds = db_race_1st_odds(self.totalRaceList[i])
            grade = db_race_grade(self.totalRaceList[i])
            analysis_train.append([odds, grade])
            logger.info("analysis data get ... {0} / {1}".format(i, self.totalRaceNum))

        # 計測終了
        time_end = time.perf_counter()

        logger.info("========================================")
        logger.info("encoding time = {0} [sec]".format(time_end - time_sta))
        # logger.info("Analysis List [odds, grade] = {0}".format([odds, grade]))
        
        return self.totalXList, self.totaltList, analysis_train
