# AI 学習用データの作成
# DB からデータを標準化し、学習データX と 教師データt の対となるリストを作成する
# 出力先 ./dst/learningList/X.pickle, t.pickle
# > python ./src/deepLearning/encoding/scrapingDataNrm.py

import pickle
import os
import configparser

# load config
config = configparser.ConfigParser()
config.read('./src/path.ini')
path_learningList = config.get('nn', 'path_learningList')
path_log = path_log = config.get('common', 'path_log')

from getFromDB import *
from encodingXClass import *

# 学習テーブル, 教師テーブル取得
# 学習用データ生成条件取得
# テスト用データ生成条件
from table import *

def save_nn_data(pkl_name, data): 
    # 保存先フォルダの存在確認
    os.makedirs(path_learningList, exist_ok=True)

    logger.info("Save {0}{1}".format(path_learningList, pkl_name))
    with open(path_learningList + pkl_name, 'wb') as f:
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
    save_nn_data(X_train_file_name, x_train)
    save_nn_data(t_train_file_name, t_train)
    save_nn_data(analysis_train_file_name, analysis_train)

    save_nn_data(X_test_file_name, x_test)
    save_nn_data(t_test_file_name, t_test)
    save_nn_data(analysis_test_file_name, analysis_test)
