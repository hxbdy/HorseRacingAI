# AI 学習用データの作成
# すでに生成済みの学習データX の末尾に新規クラスを追加するためのコード
# 対象のみを DB から標準化し、学習データX と 教師データt の対となるリストを作成する
# 同一のクラスがすでに導入されていても無条件で学習データに追加するので意図しないデータにならないように整合性には注意
# 読込及び出力先 ./dst/learningList/X.pickle, t.pickle
# > python ./src/deepLearning/encoding/appendDataNrm.py

import pickle
import os
import configparser

from getFromDB import *
from encodingXClass import *

# 学習テーブル, 教師テーブル取得
# 学習用データ生成条件取得
# テスト用データ生成条件
from table import *

# load config
config = configparser.ConfigParser()
config.read('./src/path.ini')
path_learningList = config.get('nn', 'path_learningList')
path_log = config.get('common', 'path_log')

def save_nn_data(pkl_name, data): 
    # 保存先フォルダの存在確認
    os.makedirs(path_learningList, exist_ok=True)

    logger.info("Save {0}{1}".format(path_learningList, pkl_name))
    with open(path_learningList + pkl_name, 'wb') as f:
        pickle.dump(data, f)

if __name__ == "__main__":

    # X.pickle, t.pickle 読込
    with open(path_learningList + t_train_file_name, 'rb') as f:
        t_train = pickle.load(f)
    with open(path_learningList + X_train_file_name, 'rb') as f:
        x_train = pickle.load(f)
    with open(path_learningList + t_test_file_name, 'rb') as f:
        t_test = pickle.load(f)
    with open(path_learningList + X_test_file_name, 'rb') as f:
        x_test = pickle.load(f)

    # XclassTbl に以下クラスを追加する
    # これ以外のクラスの標準化はスキップする(従来の結果をそのまま引き継ぐ)
    add_class = ParentBradleyTerryClass
    
    # 学習用データ
    logger.info("========================================")
    total_train_list = MgrClass(start_year = start_year_train, end_year = end_year_train, XclassTbl = XTbl, tclassTbl = tTbl, limit = limit_train)
    total_train_list.set_totalList(x_train, t_train)
    x_train, t_train, analysis_train = total_train_list.getAppendTotalList(add_class)

    # 学習確認用テストデータ
    logger.info("========================================")
    total_test_list = MgrClass(start_year = start_year_test, end_year = end_year_test, XclassTbl = XTbl, tclassTbl = tTbl, limit = limit_test)
    total_test_list.set_totalList(x_test, t_test)
    x_test, t_test, analysis_test = total_test_list.getAppendTotalList(add_class)

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

    logger.info("========================================")
    logger.info("Save finished")
    # 今回学習用データに追加したクラスは、table.py に定義されている各テーブルにも追記してください
    logger.info("Append {0} to each table -> XTbl, chgXTbl, predict_XTbl".format(add_class.__name__))
