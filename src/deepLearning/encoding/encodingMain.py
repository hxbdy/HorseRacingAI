# AI 学習用データの作成
# DB からデータを取得して、学習データX と 教師データt の対となるリストを作成する
# start_year <= data <= end_year のレースから limit 件取得する

import shutil
import logging

from Encoder_Mgr         import MgrClass
from table               import XTbl, tTbl
from deepLearning_common import encoding_serial_dir_path, encoding_save_nn_data, encoding_newest_dir_path
from debug               import stream_hdl, file_hdl
from file_path_mgr       import path_ini

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("output"))

if __name__ == "__main__":
    
    # エンコード
    logger.info("========================================")
    total_train_list = MgrClass(start_year = 1800, end_year = 2023, XclassTbl = XTbl, tclassTbl = tTbl, limit = -1)
    x_data, t_data = total_train_list.getTotalList()

    # 書き込み
    logger.info("========================================")

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
