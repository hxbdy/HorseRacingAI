import pickle
import os
import shutil
import configparser
import datetime
import numpy as np

from iteration_utilities import deepflatten

from table import t_train_file_name, X_train_file_name, t_test_file_name, X_test_file_name

from debug import stream_hdl, file_hdl

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("output"))

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
        len_row = len(t_train)
        t_train = np.array(list(deepflatten(t_train))).reshape(len_row, -1)
    with open(dir_path + X_train_file_name, 'rb') as f:
        x_train = pickle.load(f)
        len_row =len(x_train)
        x_train = np.array(list(deepflatten(x_train))).reshape(len_row, -1)
    with open(dir_path + t_test_file_name, 'rb') as f:
        t_test = pickle.load(f)
        len_row =len(t_test)
        t_test = np.array(list(deepflatten(t_test))).reshape(len_row, -1)
    with open(dir_path + X_test_file_name, 'rb') as f:
        x_test = pickle.load(f)
        len_row =len(x_test)
        x_test = np.array(list(deepflatten(x_test))).reshape(len_row, -1)
    logger.info("x_train = {0}, t_train = {1}, x_test = {2}, t_test = {3}".format(x_train.shape, t_train.shape, x_test.shape, t_test.shape))
    return (x_train, t_train), (x_test, t_test)

# スタート年、終了年、件数、生成に使ったクラスや条件を保存しておく
# TODO:コピーのタイミングを早める。
# エンコード中にtable.pyを編集する可能性があるため
def encoding_save_condition(dir_path):
    shutil.copy("./src/deepLearning/table.py", dir_path)
    # 保管場所もtxtで保持しておく
    with open(dir_path + "original_path.txt", 'w') as f:
        f.write("original_path = " + dir_path)
