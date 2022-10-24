import pickle
import os
import shutil
import configparser
import datetime
import numpy as np
import itertools

from debug import *
from table import *

# 連番保存フォルダまでのパスを取得する
def encoding_serial_dir_path(path_root):
    # 今日の日付フォルダ作成
    dt_now = datetime.datetime.now()
    dt_now = dt_now.strftime('%Y%m%d')
    os.makedirs(path_root + dt_now + '/', exist_ok=True)
    # 連番フォルダパス作成
    dir_list = os.listdir(path_root + dt_now)
    cnt = 0
    for dir_name in dir_list:
        if cnt <= int(dir_name):
            cnt = int(dir_name) + 1
    cnt = str(cnt)
    save_dir_path = path_root + dt_now + '/' + cnt + '/'
    return save_dir_path

# 学習済みデータの最新フォルダまでのパスを返す
def encoding_newest_dir_path():
    # newest フォルダパス取得
    config = configparser.ConfigParser()
    config.read('./src/path.ini', 'UTF-8')
    path_learningList = config.get('nn', 'path_learningList')
    os.makedirs(path_learningList, exist_ok=True)
    return path_learningList

# 学習済みパラメータの最新フォルダまでのパスを返す
def dl_newest_dir_path():
    # newest フォルダパス取得
    config = configparser.ConfigParser()
    config.read('./src/path.ini', 'UTF-8')
    path_learningList = config.get('nn', 'path_trainedParam')
    os.makedirs(path_learningList, exist_ok=True)
    return path_learningList

def encoding_save_nn_data(save_dir_path, file_name, data): 
    # 保存先フォルダの存在確認
    os.makedirs(save_dir_path, exist_ok=True)
    logger.info("Save {0}{1}".format(save_dir_path, file_name))
    with open(save_dir_path + file_name, 'wb') as f:
        pickle.dump(data, f)

# 指定パスから学習データを読み込む
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
# TODO:生成条件txtを作る
def encoding_save_condition(dir_path):
    shutil.copy("./src/deepLearning/table.py", dir_path)

# multi_x をnumpy 2次元にして返す
def dl_flat2d(multi_x):
    flat_x = []
    for i in multi_x:
        flat_x.append(list(itertools.chain.from_iterable(i)))
    flat_x = np.array(flat_x)
    return flat_x
    