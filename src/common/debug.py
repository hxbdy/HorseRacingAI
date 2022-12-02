import logging
import configparser
import os

# debug initialize
# LEVEL : DEBUG < INFO < WARNING < ERROR < CRITICAL

# コンソールにログを出力したいときはこれを呼んでハンドラをロガーに登録してください
def stream_hdl(level, output_format='%(asctime)s %(filename)18s PID:%(process)5d [%(levelname)s] %(message)s'):
    # コンソール用ハンドラ作成
    handler = logging.StreamHandler()
    # コンソール出力するログレベルの設定
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(output_format))
    return handler

# ファイルにログを出力したいときはこれを呼んでハンドラをロガーに登録してください
def file_hdl(file_name, level = logging.DEBUG):
    # load config
    config = configparser.ConfigParser()
    config.read('./src/path.ini', 'UTF-8')
    
    if file_name == "output":
        path_log = config.get('common', 'path_log')
    else:
        path_log = config.get('common', 'path_root_log')
        os.makedirs(path_log, exist_ok=True)
        path_log += file_name + ".log"


    # log出力ファイルのクリア
    # TODO: 現在、実行してもログはクリアされない
    # if file_name == "output":
    #     with open(path_log, mode = 'w'):
    #         pass

    # ファイル出力用ハンドラ作成
    handler = logging.FileHandler(filename=path_log)
    
    # ファイル出力するログレベルの設定
    # log フォーマット
    output_format = '%(asctime)s %(filename)18s PID:%(process)5d [%(levelname)s] %(message)s'
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(output_format))
    return handler
