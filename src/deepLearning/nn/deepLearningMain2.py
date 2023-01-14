# coding: utf-8

# マルチレイヤ対応版学習
# TODO: パラメータのセーブ、ロード機能

import shutil
from matplotlib import pyplot as plt

from multi_layer_net_extend import MultiLayerNetExtend
from trainer import Trainer

from file_path_mgr import path_ini
from encoding_common import encoding_load, encoding_serial_dir_path

# 学習パラメータの保存先取得
path_root_trainedParam = path_ini('nn', 'path_root_trainedParam')
serial_dir_path = encoding_serial_dir_path(path_root_trainedParam)

# 学習に使うエンコードを学習済みのパラメータを保存するフォルダにもコピーしておく
# newest学習データの読込
path_learningList = path_ini('nn', 'path_learningList')
shutil.copytree(path_learningList, serial_dir_path + "learningList/")

x_train, t_train, x_test, t_test = encoding_load(path_learningList)

def __train(lr, weight_decay, epocs=100):
    network = MultiLayerNetExtend(input_size=x_train.shape[1], hidden_size_list=[40],
                            output_size=t_train.shape[1], weight_decay_lambda=weight_decay, use_batchnorm=True)
    trainer = Trainer(network, x_train, t_train, x_test, t_test,
                      epochs=epocs, mini_batch_size=5,
                      optimizer='sgd', optimizer_param={'lr': lr}, verbose=True)
    trainer.train()

    return trainer.test_acc_list, trainer.train_acc_list

# 探索したハイパーパラメータの範囲を指定===============
# パラメータの最適値は analysis_hyperParamOpt.py で探索可能です
weight_decay = 1.506259451432141e-06
lr           = 0.0018246327811189563
# ================================================

test_acc_list, train_acc_list = __train(lr, weight_decay)
print("test acc:" + str(test_acc_list[-1]))

plt.figure() # 新規ウインドウ
plt.title("acc")
plt.plot(train_acc_list, label="train")
plt.plot(test_acc_list, label="test")
plt.legend() # 凡例表示(labelで指定したテキストの表示)

plt.show()
