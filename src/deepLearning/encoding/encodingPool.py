# AI 学習用データの作成
# DB からデータを取得して、学習データX と 教師データt の対となるリストを作成する
# start_year <= data <= end_year のレースから limit 件取得する

import shutil
import multiprocessing
from multiprocessing import Pool, Queue
from logging.handlers import QueueHandler, QueueListener

from rich.progress import track

from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from NetkeibaDB_IF       import NetkeibaDB_IF
from table               import XTbl, tTbl
from deepLearning_common import encoding_serial_dir_path, encoding_save_nn_data, encoding_newest_dir_path
from file_path_mgr       import path_ini

def encode(encoder, race_id_list):

    # 結果保存リスト
    result_list = []

    # エンコードクラス生成
    instance = encoder()

    # マルチプロセス実行なので、各エンコードクラスは子プロセスにて実行する
    instance.is_child = True

    for race_id in track(race_id_list, description="[bold green]{0:25s} encoding... ".format(instance.__class__.__name__)):
        # エンコード対象のrace_idをセットする
        instance.set(race_id)
        # 標準化まで行い結果を取得
        x_tmp = instance.adj()
        result_list.append(x_tmp)
    
    return result_list

if __name__ == "__main__":
    
    # エンコード予定のrace_idリストをDBから取得
    # (start_year <= 取得範囲 <=  end_year) の race_id
    nf = NetkeibaDB_IF("RAM")
    race_id_list = nf.db_race_list_id(start_year = 1800, end_year = 2023, limit = -1, pattern = False)
    # logger.debug(race_id_list)

    # プロセスをエンコーダ予定の数だけ用意
    p = Pool(len(XTbl) + len(tTbl))

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

    logger.debug("encode x_data: len({0}) {1}".format(len(x_data), x_data))
    logger.debug("encode t_data: len({0}) {1}".format(len(t_data), t_data))

    # プロセスを閉じる
    p.close()

    # ログリスナーを閉じる
    listener.stop()

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
