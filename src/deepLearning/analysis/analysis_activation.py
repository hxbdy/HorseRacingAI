# 隠れ層のアクティベーションを確認する
# [0-1]の間で広がった分布が理想的とされている
# 参考: 『ゼロから作るDeep Learning』 6.2 重みの初期値

import numpy as np
import matplotlib.pyplot as plt

from deepLearning_common import encoding_load


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def ReLU(x):
    return np.maximum(0, x)


def tanh(x):
    return np.tanh(x)
    
# エンコード済みデータを使用する
input_data, _, _, _ = encoding_load()
# input_data = np.random.randn(1000, 100)

node_num = input_data.shape[1]  # 各隠れ層のノード（ニューロン）の数
hidden_layer_size = 5  # 隠れ層が5層
activations = {}  # ここにアクティベーションの結果を格納する

x = input_data

for i in range(hidden_layer_size):
    if i != 0:
        x = activations[i-1]

    # 初期値パターン
    # w = np.random.randn(node_num, node_num) * 1 # std : 1
    # w = np.random.randn(node_num, node_num) * 0.01 # std : 0.01
    # w = np.random.randn(node_num, node_num) * np.sqrt(1.0 / node_num) # Xavier
    w = np.random.randn(node_num, node_num) * np.sqrt(2.0 / node_num) # He


    a = np.dot(x, w)


    # 活性化関数パターン
    # z = sigmoid(a)
    z = ReLU(a)
    # z = tanh(a)

    activations[i] = z

# ヒストグラムを描画
for i, a in activations.items():
    plt.subplot(1, len(activations), i+1)
    plt.title(str(i+1) + "-layer")
    if i != 0: plt.yticks([], [])
    # plt.xlim(0.1, 1)
    # plt.ylim(0, 7000)
    plt.hist(a.flatten(), 30, range=(0,1))
plt.show()
