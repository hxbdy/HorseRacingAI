# AI 学習用データの作成
# DB からデータを取得して、学習データX と 教師データt の対となるリストを作成する
# start_year <= data <= end_year のレースから limit 件取得する

import copy
import shutil
import multiprocessing
from multiprocessing import Pool, Queue
from logging.handlers import QueueHandler, QueueListener

import numpy as np
from rich.progress import track

from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from Encoder_X           import XClass
from NetkeibaDB_IF       import NetkeibaDB_IF
from table               import XTbl, tTbl
from deepLearning_common import encoding_serial_dir_path, encoding_save_nn_data, encoding_newest_dir_path
from file_path_mgr       import path_ini

# 各エンコードごとに列数は一定ではないため
# numpyの警告「ジャグ配列の使用」が出るので出力を抑制する
import warnings
warnings.resetwarnings()
warnings.simplefilter('ignore', np.VisibleDeprecationWarning)

def encode(encoder, race_id_list_org):

    # ディープコピー
    race_id_list = copy.copy(race_id_list_org)

    # 結果保存リスト
    result_list = []

    # エンコードクラス生成
    instance = encoder()

    # マルチプロセス実行なので、各エンコードクラスは子プロセスにて実行する
    instance.is_child = True

    # JockeyBradleyTerryClass は、例外的に一番大きいrace_id一つだけを入れる
    if(instance.__class__.__name__ == "JockeyBradleyTerryClass"):
        race_id_list = [max(race_id_list)]

    for race_id in track(race_id_list, description="[bold green]{0:25s} encoding... ".format(instance.__class__.__name__)):
        # エンコード対象のrace_idをセットする
        instance.set(race_id)
        # 標準化まで行い結果を取得
        x_tmp = instance.adj()
        result_list.append(x_tmp)
    
    return result_list

def race_id_list_under_sampling(race_id_list):
    """アンダーサンプリング
    """

    # エンコード
    t_result = encode(tTbl[0], race_id_list)

    # 最小件数の計算
    np_t_result = np.array(t_result).reshape(-1, XClass.pad_size)
    np_t_result = np.sum(np_t_result, axis=0)
    min_t_result = np.min(np_t_result)

    # 各馬番が正解となる件数を統一する
    nf = NetkeibaDB_IF("RAM")
    under_race_id_list = []
    rank_cnt_list = [0] * XClass.pad_size
    for race_id in race_id_list:
        # race_id で1位の馬番を取得
        horse_index = nf.db_race_list_id_under_sampling(race_id)

        # 1位の数がmin_t_result件になるようにする
        if horse_index is not None:
            if horse_index <= XClass.pad_size:
                if rank_cnt_list[horse_index-1] != min_t_result:
                    under_race_id_list.append(race_id)
                    rank_cnt_list[horse_index-1] += 1


    logger.debug("under_race_id_list = {0}".format(under_race_id_list))
    logger.debug("rank_cnt_list      = {0}".format(rank_cnt_list))

    return under_race_id_list


def multi_encode(start_year = 1800, end_year = 2020, limit = -1, pattern = False, save = False):
    """マルチプロセスでエンコード実行して結果を返す"""

    # エンコード予定のrace_idリストをDBから取得
    # (start_year <= 取得範囲 <=  end_year) の race_id
    nf = NetkeibaDB_IF("RAM")
    race_id_list = nf.db_race_list_id(start_year, end_year, limit, pattern)
    del nf

    # アンダーサンプリング
    race_id_list = race_id_list_under_sampling(race_id_list)

    # プロセス用意
    # processes 指定しないことで、環境ごとの使用可能論理プロセス数を使用する
    p = Pool()

    # ログ用のキューを用意
    queue = Queue()

    # マルチプロセス用のロガーを取得
    mp_logger = multiprocessing.get_logger()
    mp_logger.setLevel(logging.WARNING)

    # マルチプロセス用のロガーにキューハンドラを追加
    mp_logger.addHandler(QueueHandler(queue))

    # マルチプロセス用キューのリスナープロセスを用意
    listener = QueueListener(queue, RichHandler(rich_tracebacks=True))
    listener.start()

    # input用
    # xとtをinputに追加
    inputs = []
    for x in XTbl:
        inputs.append((x, race_id_list))
    inputs.append((tTbl[0], race_id_list)) 

    # エンコード開始
    result = p.starmap(encode, inputs)

    # 結果をxとtに分ける
    t_data = result.pop(-1)
    x_data = result

    # 転置T
    # numpyの警告「ジャグ配列の使用」が出る
    x_data = np.array(x_data).reshape(len(XTbl), -1).T.tolist()

    logger.debug("encode x_data: len({0}) {1}".format(len(x_data), x_data))
    logger.debug("encode t_data: len({0}) {1}".format(len(t_data), t_data))

    # プロセスを閉じる
    p.close()

    # ログリスナーを閉じる
    listener.stop()

    if save:
        # 書き込み
        # 保存先パス取得
        path_root = path_ini('nn', 'path_root_learningList')

        # 連番取得
        serial_dir_path = encoding_serial_dir_path(path_root)

        # 連番フォルダにエンコード済みデータ保存
        encoding_save_nn_data(serial_dir_path, "x_data.pickle", x_data)
        encoding_save_nn_data(serial_dir_path, "t_data.pickle", t_data)

        # 最新フォルダまでのパスを取得
        newest_dir_path = encoding_newest_dir_path()

        # newestフォルダ削除
        shutil.rmtree(newest_dir_path)

        # 最新フォルダに結果をコピー
        shutil.copytree(serial_dir_path, newest_dir_path)

    return race_id_list, x_data, t_data

if __name__ == "__main__":
    race_id_list, x_data, t_data = multi_encode(start_year = 2000, end_year = 2022, limit = -1, pattern = False, save = True)
