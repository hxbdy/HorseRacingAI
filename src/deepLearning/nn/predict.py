import configparser

import TwoLayerNet

from table import predict_XTbl
from config_predict import *
from encoding_common import *

if __name__ == "__main__":
    # 行列サイズ取得のため学習データの読込
    config = configparser.ConfigParser()
    config.read('./src/path.ini')
    path_learningList = config.get('nn', 'path_learningList')
    (x_train, t_train), (x_test, t_test) = encoding_load(path_learningList)

    # 多次元になっているリストを2次元にならす
    x_train = dl_flat2d(x_train)
    t_train = dl_flat2d(t_train)
    x_test = dl_flat2d(x_test)
    t_test = dl_flat2d(t_test)

    # 保存済みパラメータ読み込み
    net = TwoLayerNet.TowLayerNet(x_train.shape[1], 40, t_train.shape[1])
    net.loadParam()

    x = []
    for func in predict_XTbl:
        # インスタンス生成
        predict = func()
        x.append(predict.adj())

    x = dl_flat2d([x])
    # print("x = ", x)

    y = net.predict(x)
    # print("y = ", y)
    print("argmax = ",y.argmax())
