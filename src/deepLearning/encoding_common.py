import pickle
import os
import shutil
import configparser
import datetime

from debug import *
from table import *

# 連番保存フォルダまでのパスを取得する
def encoding_serial_dir_path():
    # 保存先パス取得
    config = configparser.ConfigParser()
    config.read('./src/path.ini')
    path_root_learningList = config.get('nn', 'path_root_learningList')
    # 今日の日付フォルダ作成
    dt_now = datetime.datetime.now()
    dt_now = dt_now.strftime('%Y%m%d')
    os.makedirs(path_root_learningList + dt_now + '/', exist_ok=True)
    # 連番フォルダパス作成
    dir_list = os.listdir(path_root_learningList + dt_now)
    cnt = 0
    for dir_name in dir_list:
        if cnt <= int(dir_name):
            cnt = int(dir_name) + 1
    cnt = str(cnt)
    save_dir_path = path_root_learningList + dt_now + '/' + cnt + '/'
    return save_dir_path

# 最新フォルダまでのパスを返す
def encoding_newest_dir_path():
    # newest フォルダパス取得
    config = configparser.ConfigParser()
    config.read('./src/path.ini')
    path_learningList = config.get('nn', 'path_learningList')
    os.makedirs(path_learningList, exist_ok=True)
    return path_learningList

def encoding_save_nn_data(save_dir_path, file_name, data): 
    # 保存先フォルダの存在確認
    os.makedirs(save_dir_path, exist_ok=True)
    logger.info("Save {0}{1}".format(save_dir_path, file_name))
    with open(save_dir_path + file_name, 'wb') as f:
        pickle.dump(data, f)

# どのフォルダから学習データを読み込むか決定する
# デフォルトでは newest フォルダから読み込む。
# パスの指定次第では別のフォルダから読み込むことも可能
def encoding_load(dir_path):
    with open(dir_path + t_train_file_name, 'rb') as f:
        t_train = pickle.load(f)
    with open(dir_path + X_train_file_name, 'rb') as f:
        x_train = pickle.load(f)
    with open(dir_path + t_test_file_name, 'rb') as f:
        t_test = pickle.load(f)
    with open(dir_path + X_test_file_name, 'rb') as f:
        x_test = pickle.load(f)
    return (x_train, t_train), (x_test, t_test)

# スタート年、終了年、件数、生成に使ったクラスや条件を保存しておく
# !! 現状生成に使ったtable.pyをそのままコピーしているだけ
# !! 通常生成, クラス追加, 差し替え のどれから実行されたかが不明になっている
def encoding_save_condition(dir_path):
    shutil.copy("./src/deepLearning/table.py", dir_path)
