import pickle
import os
import shutil
import datetime

from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from iteration_utilities import deepflatten

from file_path_mgr import path_ini
from make_RaceInfo import raceinfo_by_raceID
import RaceInfo
import xross
np = xross.facttory_xp()

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
    path_learningList = path_ini('nn', 'path_learningList')
    os.makedirs(path_learningList, exist_ok=True)
    return path_learningList

# 学習済みパラメータの最新フォルダまでのパスを返す
def dl_newest_dir_path():
    path_learningList = path_ini('nn', 'path_trainedParam')
    os.makedirs(path_learningList, exist_ok=True)
    return path_learningList

# 今回の結果を最新フォルダにもコピーする
def dl_copy2newest(serial_dir_path):
    # 最新フォルダまでのパスを取得
    newest_dir_path = dl_newest_dir_path()
    # newestフォルダ削除
    shutil.rmtree(newest_dir_path)
    # 最新フォルダにコピー
    shutil.copytree(serial_dir_path, newest_dir_path)

def encoding_save_nn_data(save_dir_path, file_name, data): 
    # 保存先フォルダの存在確認
    os.makedirs(save_dir_path, exist_ok=True)
    logger.info("Save {0}{1}".format(save_dir_path, file_name))
    with open(save_dir_path + file_name, 'wb') as f:
        pickle.dump(data, f)

def encoding_load(dir_path=""):
    '''エンコード済み学習データを読み込む
    パスを指定しない時はpath.iniのpath_learningListから読み込む
    ATTENTION: パスを指定するときは最後にスラッシュをつけてください
    '''
    
    # パス読み込み
    if dir_path == "":
        path_learningList = path_ini('nn', 'path_learningList')
    else:
        path_learningList = dir_path

    # 学習データからは何個エンコーダを使用したかわからないため
    # 正解ラベルの行数を先に取得して、次に学習データをreshapeする
    with open(path_learningList + "t_data.pickle", 'rb') as f:
        logger.info("load learningList = {0}".format(path_learningList + "t_data.pickle"))
        e = pickle.load(f)
        t_data = np.array(list(deepflatten(e)))
        t_data = t_data.reshape(len(e), -1)
        logger.info("{0} = {1}".format("t_data.shape", t_data.shape))

    with open(path_learningList + "x_data.pickle", 'rb') as f:
        logger.info("load learningList = {0}".format(path_learningList + "x_data.pickle"))
        e = pickle.load(f)
        x_data = np.array(list(deepflatten(e)))
        x_data = x_data.reshape(t_data.shape[0], -1)
        logger.info("{0} = {1}".format("x_data.shape", x_data.shape))

    return x_data, t_data

# スタート年、終了年、件数、生成に使ったクラスや条件を保存しておく
# TODO:コピーのタイミングを早める。
# エンコード中にtable.pyを編集する可能性があるため
def encoding_save_condition(dir_path):
    shutil.copy("./src/deepLearning/table.py", dir_path)
    # 保管場所もtxtで保持しておく
    with open(dir_path + "original_path.txt", 'w') as f:
        f.write("original_path = " + dir_path)

def prob_win(value_list):
    """推測結果を出力する(ロジットモデル)
    出力内容は馬番のリストと、それぞれが一着になる確率のリスト
    return 馬番インデックスリスト(ゼロが馬番1であることに注意), (確率リスト)"""

    ls = np.array(value_list)
    ls_sorted_idx = np.argsort(-ls) # 降順のソート
    ls_sorted = ls[ls_sorted_idx]
    prob = np.exp(ls_sorted)/sum(np.exp(ls_sorted)) # 確率計算

    # cupy は format に対応していないためそのまま出力する
    # TODO: cupy 使用時の出力フォーマット整形
    if xross.isCPU():
        prob_disp = ["{:.3f}".format(i) for i in prob] # 表示桁数を制限

        logger.info(["{:^5d}".format(i) for i in ls_sorted_idx+1])
        logger.info(prob_disp)
    else:
        logger.info(ls_sorted_idx+1)
        logger.info(prob)
    return list(ls_sorted_idx), prob.tolist()

def read_RaceInfo(race_id = ""):
    """推測するレースのRaceInfoオブジェクトを読み込む
    race_id: 指定した場合、データベースから読込。無指定ならばpickleを読込
    """
    if race_id == "":
        # TODO: 読み込みに失敗したとき、情報をスクレイピングしておく旨を表示して終了する対応
        path_tmp = path_ini('common', 'path_tmp')
        with open(path_tmp, 'rb') as f:
            tmp_param: RaceInfo = pickle.load(f)
        return tmp_param
    else:
        param = raceinfo_by_raceID(str(race_id))
        return param

def write_RaceInfo(param: RaceInfo):
    """RaceInfoオブジェクトを保存
    """
    path_tmp = path_ini('common', 'path_tmp')

    # 推測用に取得したレース情報を一時保存
    with open(path_tmp, 'wb') as f:
        pickle.dump(param, f)
