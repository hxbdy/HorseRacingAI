import numpy as np
import matplotlib.pyplot as plt

from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def selfcheck(class_name, x):
    # コンソール表示上、有効桁数は2桁とする
    np.set_printoptions(precision=2)
    plt.title(class_name + " hist")
    # 最大値、最小値
    logger.info("MAX = {0}, MIN = {1}".format(np.max(x), np.min(x)))
    # メモリは0.1刻みで表示
    range_tick = [i / 10 for i in range(-5, 15)]
    plt.xticks(range_tick)
    # ヒストグラム
    # 幅は0.1刻み
    plt.hist(x, histtype='barstacked', bins=range_tick)
    plt.show()
