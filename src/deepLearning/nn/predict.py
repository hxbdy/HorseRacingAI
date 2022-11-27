# 推測する
# 予測したいレース情報は src\deepLearning\nn\config_predict.py で入力してください
# > python ./src/deepLearning/nn/predict.py

import configparser
import numpy as np
from multiprocessing import Queue

import TwoLayerNet

from table import predict_XTbl
from config_predict import *
from encoding_common import encoding_load, dl_flat2d

if __name__ == "__main__":
    # 行列サイズ取得のため学習データの読込
    config = configparser.ConfigParser()
    config.read('./src/path.ini', 'UTF-8')
    path_learningList = config.get('nn', 'path_learningList')
    (x_train, t_train), (x_test, t_test) = encoding_load(path_learningList)

    # 多次元になっているリストを2次元にならす
    x_train = dl_flat2d(x_train)
    t_train = dl_flat2d(t_train)
    x_test = dl_flat2d(x_test)
    t_test = dl_flat2d(t_test)

    # logger
    queue_log = Queue()

    # 推測用エンコード
    x = []
    for func in predict_XTbl:
        # インスタンス生成
        predict = func()
        x.append(predict.adj(queue_log))
    x = dl_flat2d([x])

    # 保存済みパラメータ読み込み
    net = TwoLayerNet.TowLayerNet(x_train.shape[1], 40, t_train.shape[1])
    net.loadParam()

    # 推測
    y = net.predict(x)
    pre = np.argsort(y) + 1

    # ソート済みの各馬番が1位になる確率
    print("predict = ", pre[0][::-1])
