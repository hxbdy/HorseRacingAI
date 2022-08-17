# coding: utf-8
import sys, os
from two_layer_net import TwoLayerNet
import numpy as np
import pickle
import pathlib

# commonフォルダ内読み込みのため
deepLearning_dir = pathlib.Path(__file__).parent
src_dir = deepLearning_dir.parent
root_dir = src_dir.parent
dir_lst = [deepLearning_dir, src_dir, root_dir]
for dir_name in dir_lst:
    if str(dir_name) not in sys.path:
        sys.path.append(str(dir_name))

OUTPUT_PATH = str(root_dir) + "\\dst\\trainedParam\\"

# データの読み込み
with open(str(root_dir) + "\\dst\\learningList\\t.pickle", 'rb') as f:
    tData = pickle.load(f)
    t_train = np.array(tData)

with open(str(root_dir) + "\\dst\\learningList\\x.pickle", 'rb') as f:
    xData = pickle.load(f)
    x_train = np.array(xData)

network = TwoLayerNet(input_size=131, hidden_size=40, output_size=24)

iters_num = 10000
train_size = x_train.shape[0]
batch_size = 1
learning_rate = 0.1

train_loss_list = []
train_acc_list = []

iter_per_epoch = max(train_size / batch_size, 1)

for i in range(iters_num):

    # 学習データ取り出し
    batch = np.random.randint(0, train_size)
    
    x_batch = x_train[batch]
    t_batch = t_train[batch]

    # shape修正
    x_batch = x_batch.reshape([batch_size, -1])
    # print("x_batch = ", x_batch)
    # print("t_batch = ", t_batch)

    # 勾配
    #grad = network.numerical_gradient(x_batch, t_batch)
    grad = network.gradient(x_batch, t_batch)
    
    # 更新
    for key in ('W1', 'b1', 'W2', 'b2'):
        network.params[key] -= learning_rate * grad[key]
    
    loss = network.loss(x_batch, t_batch)
    train_loss_list.append(loss)

    # print progress bar
    train_acc = network.accuracy(x_train, t_train)
    train_acc_list.append(train_acc)
    per = int(i / iters_num * 20)
    pro_bar = ('=' * per) + (' ' * (20 - per))
    print('\r[{0}] {1:02.03}% err={2}'.format(pro_bar, i / iters_num * 100, train_acc), end='')

# 保存先フォルダ作成
os.makedirs(OUTPUT_PATH, exist_ok=True)

# 誤差率をtxt保存
path_w=OUTPUT_PATH+'loss.txt'
f=open(path_w,mode='w')
for i in train_loss_list:
    f.write(str(i)+"\n")
f.close()

# 学習パラメータをtxt, pickle保存
for key in ('W1', 'b1', 'W2', 'b2'):
    path_w=OUTPUT_PATH+key+'.txt'
    f=open(path_w,mode='w')
    it = np.nditer(network.params[key], flags=['multi_index'], op_flags=['readwrite'])
    while not it.finished:
        idx=it.multi_index
        f.write(str(network.params[key][idx]))
        f.write("\n")
        it.iternext()
    f.close()

    with open(OUTPUT_PATH + key + ".pickle", 'wb') as f:
        pickle.dump(network.params[key], f)
    f.close()
