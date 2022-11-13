# マルチプロセス用ロガー
# リスナー側で出力用のフォーマットなど定義しておく

import logging
import configparser

def log_listener(q):

    # load config
    config = configparser.ConfigParser()
    config.read('./src/path.ini', 'UTF-8')
    path_log = config.get('common', 'path_log')

    # log出力ファイルのクリア
    # with open(path_log, mode = 'w'):
    #    pass
    
    # ログセット
    output_format = '%(asctime)s [%(levelname)s] PID:%(process)5d %(message)s'
    logger = logging.getLogger(__name__)
    h = logging.FileHandler(path_log)
    f = logging.Formatter(output_format)
    h.setFormatter(f)
    logger.addHandler(h)

    # リスナー本体
    # TODO: メモリを無限に食うバグ発生中。停止中
    while False:
        try:
            # タイムアウトはロガーが全エンコーダが完了したか判断する手段がないため設けている
            # エンコード途中にタイムアウトした場合は以降ロギングされない
            # タイムアウトを大きくすることはエンコーダに影響しないので伸ばしてもいい
            logger.handle(q.get(timeout = 10))
        except:
            print("Encode timeout")
            break
