# AI 学習用データの作成
# DB からデータを標準化し、学習データX と 教師データt の対となるリストを作成する
# start_year <= data <= end_year のレースから limit 件取得する
# USAGE : 生成条件をtable.pyで設定し以下コマンド実行
# > python ./src/deepLearning/encoding/scrapingDataNrm.py

from getFromDB import *
from encodingXClass import *
from table import *
from encoding_common import *
import shutil

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

    # 連番フォルダに保存
    # 連番取得
    serial_dir_path = encoding_serial_dir_path()
    encoding_save_nn_data(serial_dir_path, X_train_file_name, x_train)
    encoding_save_nn_data(serial_dir_path, t_train_file_name, t_train)
    encoding_save_nn_data(serial_dir_path, analysis_train_file_name, analysis_train)
    encoding_save_nn_data(serial_dir_path, X_test_file_name, x_test)
    encoding_save_nn_data(serial_dir_path, t_test_file_name, t_test)
    encoding_save_nn_data(serial_dir_path, analysis_test_file_name, analysis_test)

    # 生成条件の保存
    encoding_save_condition(serial_dir_path)

    # 最新フォルダまでのパスを取得
    newest_dir_path = encoding_newest_dir_path()
    # newestフォルダ削除
    shutil.rmtree(newest_dir_path)
    # 最新フォルダに結果をコピー
    shutil.copytree(serial_dir_path, newest_dir_path)
