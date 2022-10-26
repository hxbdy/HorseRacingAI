import logging
import configparser

# load config
config = configparser.ConfigParser()
config.read('./src/path.ini', 'UTF-8')
path_log = config.get('common', 'path_log')

# log出力ファイルのクリア
with open(path_log, mode = 'w'):
    pass

# log フォーマット
output_format = '%(asctime)s %(filename)20s PID:%(process)5d [%(levelname)s] %(message)s'

# debug initialize
# LEVEL : DEBUG < INFO < WARNING < ERROR < CRITICAL
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# コンソール用ハンドラ作成
handler1 = logging.StreamHandler()
# コンソール出力するログレベルの設定
handler1.setLevel(logging.INFO)
handler1.setFormatter(logging.Formatter(output_format))

# ファイル出力用ハンドラ作成
handler2 = logging.FileHandler(filename=path_log)
# ファイル出力するログレベルの設定
handler2.setLevel(logging.DEBUG)
handler2.setFormatter(logging.Formatter(output_format))

#loggerに2つのハンドラを設定
logger.addHandler(handler1)
logger.addHandler(handler2)
