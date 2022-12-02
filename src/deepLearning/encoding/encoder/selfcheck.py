import numpy as np
import matplotlib.pyplot as plt

from debug import stream_hdl
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))

def selfcheck(x):
    # コンソール表示上、有効桁数は2桁とする
    np.set_printoptions(precision=2)
    # 最大値、最小値
    logger.info("MAX = {0}, MIN = {1}".format(np.max(x, axis=1), np.min(x, axis=1)))
    # ヒストグラム
    plt.hist(x)
    plt.show()
