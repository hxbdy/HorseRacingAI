# coding: utf-8

# マルチレイヤ対応版学習

import shutil
from matplotlib import pyplot as plt

from multi_layer_net_extend import MultiLayerNetExtend
from trainer                import Trainer
from util                   import shuffle_dataset
from file_path_mgr          import path_ini
from deepLearning_common    import encoding_load, encoding_serial_dir_path, dl_copy2newest, encoding_save_nn_data

# 学習パラメータの保存先取得
path_root_trainedParam = path_ini('nn', 'path_root_trainedParam')
serial_dir_path = encoding_serial_dir_path(path_root_trainedParam)

# 学習に使うエンコードを学習済みのパラメータを保存するフォルダにもコピーしておく
# newest学習データの読込
path_learningList = path_ini('nn', 'path_learningList')
shutil.copytree(path_learningList, serial_dir_path + "learningList/")

x_data, t_data = encoding_load(path_learningList)

# データシャッフル
rate = 0.8
train_num = int(x_data.shape[0] * rate)
x_data, t_data = shuffle_dataset(x_data, t_data)
x_train = x_data[:train_num]
t_train = t_data[:train_num]
x_test = x_data[train_num:]
t_test = t_data[train_num:]

def __train(lr, weight_decay, epocs=500):
    network = MultiLayerNetExtend(input_size=x_train.shape[1], hidden_size_list=[200, 75],
                            output_size=t_train.shape[1], weight_decay_lambda=weight_decay,
                            use_dropout=False, activation='sigmoid', weight_init_std='sigmoid')

    # 学習前のパラメータをnpy形式で保存
    network.save(serial_dir_path + "init/")

    trainer = Trainer(network, x_train, t_train, x_test, t_test,
                      epochs=epocs, mini_batch_size=50,
                      optimizer='sgd', optimizer_param={'lr': lr}, verbose=True)
    
    # 学習
    trainer.train()

    # 学習後のパラメータをnpy形式で保存
    network.save(serial_dir_path + "final/")

    # networkをpickle形式で保存
    encoding_save_nn_data(serial_dir_path, "network.pickle", network)

    # 最新フォルダにも結果をコピー
    dl_copy2newest(serial_dir_path)

    return trainer.test_acc_list, trainer.train_acc_list

# 探索したハイパーパラメータの範囲を指定===============
# パラメータの最適値は analysis_hyperParamOpt.py で探索可能
weight_decay = 8.865554344288922e-05
lr           = 0.0017072433461073357
# ================================================

test_acc_list, train_acc_list = __train(lr, weight_decay, epocs=500)
print("train acc:" + str(train_acc_list[-1]))

plt.figure() # 新規ウインドウ
plt.title("acc")
plt.plot(train_acc_list, label="train")
plt.plot(test_acc_list, label="test")
plt.legend() # 凡例表示(labelで指定したテキストの表示)

plt.show()
