# coding: utf-8

# マルチレイヤ対応版学習
# ハイパーパラメータの最適値を探す
# 100回捜索してトップ20を最後にグラフで出力する

import shutil
import numpy as np
import matplotlib.pyplot as plt

from multi_layer_net_extend import MultiLayerNetExtend
from util import shuffle_dataset
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

x_train, t_train = encoding_load(path_learningList)

# 高速化のため訓練データの削減
# x_train = x_train[:500]
# t_train = t_train[:500]

# 検証データの分離
validation_rate = 0.20
validation_num = int(x_train.shape[0] * validation_rate)
x_train, t_train = shuffle_dataset(x_train, t_train)
x_val = x_train[:validation_num]
t_val = t_train[:validation_num]
x_train = x_train[validation_num:]
t_train = t_train[validation_num:]


def __train(lr, weight_decay, epocs=100):
    network = MultiLayerNetExtend(input_size=x_train.shape[1], hidden_size_list=[40],
                            output_size=t_train.shape[1], weight_decay_lambda=weight_decay, use_batchnorm=True, use_dropout=True)
    trainer = Trainer(network, x_train, t_train, x_val, t_val,
                      epochs=epocs, mini_batch_size=5,
                      optimizer='sgd', optimizer_param={'lr': lr}, verbose=True)
    trainer.train()

    return trainer.test_acc_list, trainer.train_acc_list


# ハイパーパラメータのランダム探索======================================
optimization_trial = 100
results_val = {}
results_train = {}
for i in range(optimization_trial):
    # 探索したハイパーパラメータの範囲を指定===============
    weight_decay = 10 ** np.random.uniform(-8, -4)
    lr = 10 ** np.random.uniform(-6, -2)
    # ================================================

    val_acc_list, train_acc_list = __train(lr, weight_decay)
    print("attempts No." + str(i) +" val acc:" + str(val_acc_list[-1]) + " | lr:" + str(lr) + ", weight decay:" + str(weight_decay))
    key = "lr:" + str(lr) + ", weight decay:" + str(weight_decay)
    results_val[key] = val_acc_list
    results_train[key] = train_acc_list

# グラフの描画========================================================
print("=========== Hyper-Parameter Optimization Result ===========")
graph_draw_num = 20
col_num = 5
row_num = int(np.ceil(graph_draw_num / col_num))
i = 0

for key, val_acc_list in sorted(results_val.items(), key=lambda x:x[1][-1], reverse=True):
    print("Best-" + str(i+1) + "(val acc:" + str(val_acc_list[-1]) + ") | " + key)

    plt.subplot(row_num, col_num, i+1)
    plt.title("Best-" + str(i+1))
    plt.ylim(0.0, 1.0)
    if i % 5: plt.yticks([])
    plt.xticks([])
    x = np.arange(len(val_acc_list))
    plt.plot(x, val_acc_list)
    plt.plot(x, results_train[key], "--")
    i += 1

    if i >= graph_draw_num:
        break

plt.show()
