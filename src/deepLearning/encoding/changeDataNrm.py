# AI 学習用データの作成
# すでに生成済みの学習データX と 教師データtの一部データを差し替えるためのコード
# 対象のみを DB から標準化し、学習データX と 教師データt の対となるリストを作成する
# USAGE : chgXTbl の変更したい場所のNoneをクラス名に差し替えて以下実行
# > python ./src/deepLearning/encoding/changeDataNrm.py

import configparser

from getFromDB import *
from encodingXClass import *
from table import *
from encoding_common import *

if __name__ == "__main__":
    # load config
    config = configparser.ConfigParser()
    config.read('./src/path.ini')
    path_learningList = config.get('nn', 'path_learningList')

    # 最新 X.pickle, t.pickle 読込
    (x_train, t_train), (x_test, t_test) = encoding_load(path_learningList)
    
    # 学習用データ
    logger.info("========================================")
    logger.info("generate train data")
    total_train_list = MgrClass(start_year = start_year_train, end_year = end_year_train, XclassTbl = chgXTbl, tclassTbl = tTbl, limit = limit_train)
    total_train_list.set_totalList(x_train, t_train)
    x_train, t_train, analysis_train = total_train_list.getTotalList()

    # 学習確認用テストデータ
    logger.info("========================================")
    logger.info("generate test data")
    total_test_list = MgrClass(start_year = start_year_test, end_year = end_year_test, XclassTbl = chgXTbl, tclassTbl = tTbl, limit = limit_test)
    total_test_list.set_totalList(x_test, t_test)
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
    