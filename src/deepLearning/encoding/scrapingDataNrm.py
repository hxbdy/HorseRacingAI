# AI 学習用データの作成
# DB からデータを標準化し、学習データX と 教師データt の対となるリストを作成する
# start_year <= data <= end_year のレースから limit 件取得する
# USAGE : 生成条件をtable.pyで設定し以下コマンド実行
# > python ./src/deepLearning/encoding/scrapingDataNrm.py

import shutil
import logging

from Encoder_Mgr import MgrClass
from table import start_year_train, end_year_train, \
                  XTbl, tTbl, \
                  start_year_test, end_year_test, \
                  limit_train, limit_test, \
                  analysis_train_file_name, analysis_test_file_name, \
                  encoded_file_name_list
from encoding_common import encoding_serial_dir_path, encoding_save_nn_data, encoding_save_condition, encoding_newest_dir_path
from debug import stream_hdl, file_hdl
from file_path_mgr import path_ini

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("output"))

if __name__ == "__main__":
    
    # 学習用データ
    logger.info("========================================")
    logger.info("generate train data")
    total_train_list = MgrClass(start_year = start_year_train, end_year = end_year_train, XclassTbl = XTbl, tclassTbl = tTbl, limit = limit_train)
    x_train, t_train, analysis_train = total_train_list.getTotalList()

    # 学習確認用テストデータ
    logger.info("========================================")
    logger.info("generate test data")
    total_test_list = MgrClass(start_year = start_year_test, end_year = end_year_test, XclassTbl = XTbl, tclassTbl = tTbl, limit = limit_test)
    x_test, t_test, analysis_test = total_test_list.getTotalList()

    # 書き込み
    logger.info("========================================")

    # 保存先パス取得
    path_root = path_ini('nn', 'path_root_learningList')

    # 連番取得
    serial_dir_path = encoding_serial_dir_path(path_root)
    
    # 連番フォルダにエンコード済みデータ保存
    encoded_list = [x_train, t_train, x_test, t_test]
    for i in range(len(encoded_file_name_list)):
        encoding_save_nn_data(serial_dir_path, encoded_file_name_list[i], encoded_list[i])

    # 連番フォルダに解析用データ保存
    encoding_save_nn_data(serial_dir_path, analysis_train_file_name, analysis_train)
    encoding_save_nn_data(serial_dir_path, analysis_test_file_name, analysis_test)

    # 生成条件の保存
    encoding_save_condition(serial_dir_path)

    # 最新フォルダまでのパスを取得
    newest_dir_path = encoding_newest_dir_path()
    # newestフォルダ削除
    shutil.rmtree(newest_dir_path)
    # 最新フォルダに結果をコピー
    shutil.copytree(serial_dir_path, newest_dir_path)
