# AI 学習用データの作成
# DB からデータを標準化し、学習データX と 教師データt の対となるリストを作成する
# 出力先 ./dst/learningList/X.pickle, t.pickle
# > python ./src/deepLearning/encoding/scrapingDataNrm.py

import pickle
import os
import configparser
import datetime
import shutil

# load config
config = configparser.ConfigParser()
config.read('./src/path.ini')
path_learningList = config.get('nn', 'path_learningList')
path_log = config.get('common', 'path_log')
path_root_learningList = config.get('nn', 'path_root_learningList')

from getFromDB import *
from encodingXClass import *

# 学習テーブル, 教師テーブル取得
# 学習用データ生成条件取得
# テスト用データ生成条件
from table import *

# DBから生成した学習/テストデータを保存する
# 後で学習精度の比較を行うため上書きしない
# 保存先 ./dst/learningList/日付/連番
# 生成時の各種設定値もtxtで保存しておく
def save_nn_data(pkl_name, save_dir_path, data): 
    # 保存先フォルダの存在確認
    os.makedirs(save_dir_path, exist_ok=True)

    logger.info("Save {0}{1}".format(save_dir_path, pkl_name))
    with open(save_dir_path + pkl_name, 'wb') as f:
        pickle.dump(data, f)

if __name__ == "__main__":
    # start_year <= data <= end_year のレースから limit 件取得する
    # ここで生成したデータは ./src/deepLearning/changeDataNrm.py で差し替え可能です
    # MgrClass の生成条件 start_year, end_year, limit は統一すること
    
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

    # 出力ファイル名フォーマット
    # X_{開始年}-{終了年}-{件数}

    dt_now = datetime.datetime.now()
    dt_now = dt_now.strftime('%Y%m%d')

    os.makedirs(path_root_learningList + dt_now + '/', exist_ok=True)

    dir_list = os.listdir(path_root_learningList + dt_now)
    cnt = 0
    for dir_name in dir_list:
        if cnt <= int(dir_name):
            cnt = int(dir_name) + 1
    cnt = str(cnt)
    save_dir_path = path_root_learningList + dt_now + '/' + cnt + '/'

    save_nn_data(X_train_file_name, save_dir_path, x_train)
    save_nn_data(t_train_file_name, save_dir_path, t_train)
    save_nn_data(analysis_train_file_name, save_dir_path, analysis_train)

    save_nn_data(X_test_file_name, save_dir_path, x_test)
    save_nn_data(t_test_file_name, save_dir_path, t_test)
    save_nn_data(analysis_test_file_name, save_dir_path, analysis_test)

    # 最新版としても保存
    # newestフォルダクリア
    shutil.rmtree(path_learningList)
    os.mkdir(path_learningList)

    save_nn_data(X_train_file_name, path_learningList, x_train)
    save_nn_data(t_train_file_name, path_learningList, t_train)
    save_nn_data(analysis_train_file_name, path_learningList, analysis_train)

    save_nn_data(X_test_file_name, path_learningList, x_test)
    save_nn_data(t_test_file_name, path_learningList, t_test)
    save_nn_data(analysis_test_file_name, path_learningList, analysis_test)
