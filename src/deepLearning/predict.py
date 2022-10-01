from table import predict_XTbl
from config_predict import *

if __name__ == "__main__":

    # 保存済みパラメータ読み込み
    #net = TwoLayerNet.TowLayerNet(131,50,24)
    #net.loadParam()

    x = []
    for func in predict_XTbl:
        predict = func()
        if func == PredictHorseAgeClass:
            x.append(predict.adj(d0))
        else:
            x.append(predict.adj())

    print("x = ", x)
    # x = list(deepflatten(x))

    # y = 各馬が1位になる確率
    # y = net.predict(x)
