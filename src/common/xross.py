# 行列演算に使用するライブラリを選ぶ
# numpy(use CPU) or cupy(use GPU)
# どちらを使うかは private.ini で設定

import importlib
import logging

from file_path_mgr import private_ini
from debug import stream_hdl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(stream_hdl(logging.INFO))

def get_calc_device():
    return private_ini('nn', 'calculator')

def factory_np():
    return importlib.import_module('numpy')

def factory_cp():
    cp = importlib.import_module('cupy')
    # メモリプール有効
    # malloc/free 時のCPUとの同期を回避
    cp.cuda.set_allocator(cp.cuda.MemoryPool().malloc)
    return cp

def facttory_xp():
    """ Returns: imported instance of cupy or numpy.
    hint: write private.ini/nn/calculator
    """
    calculator = get_calc_device()

    if calculator == "GPU":
        logger.debug("matrix calculator -> GPU")
        return factory_cp()
    else:
        logger.debug("matrix calculator -> CPU")
        return factory_np()

def move2RAM(data):
    """計算結果をRAMで保持できる型に変換する
    cupyで計算した場合、GPU RAMで保持しているため
    グラフ描画時などはデータをGPU RAMからRAMへ移動させる変換が必要
    """
    calculator = get_calc_device()
    if calculator == "GPU":
        if type(data) == int:
            return data.get()
        elif type(data) == list:
            ret = []
            for i in data:
                ret.append(i.get())
            return ret
        else:
            logger.warn("Unknown Type : {0}".format(type(data)))
            return data
    else:
        return data
