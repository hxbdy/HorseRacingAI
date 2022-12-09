# 推測する
# 予測したいレース情報は src\deepLearning\nn\config_predict.py で入力してください
# > python ./src/deepLearning/nn/predict.py

import configparser
import numpy as np

from iteration_utilities import deepflatten

import TwoLayerNet

from table import predict_XTbl
from config_predict import *
from encoding_common import encoding_load

if __name__ == "__main__":
    # 行列サイズ取得のため学習データの読込
    config = configparser.ConfigParser()
    config.read('./src/path.ini', 'UTF-8')
    path_learningList = config.get('nn', 'path_learningList')
    (x_train, t_train), (x_test, t_test) = encoding_load(path_learningList)

    # 推測用エンコード
    x = []
    for func in predict_XTbl:
        # インスタンス生成
        predict = func()
        x.append(predict.adj())
    x = np.array(list(deepflatten(x))).reshape(1, -1)

    # 保存済みパラメータ読み込み
    net = TwoLayerNet.TowLayerNet(x_train.shape[1], 40, t_train.shape[1])
    net.loadParam()

    # 推測
    y = net.predict(x)
    print("y = ", y)

    pre = np.argsort(y) + 1

    # ソート済みの各馬番が1位になる確率
    print("predict = ", pre[0][::-1])
