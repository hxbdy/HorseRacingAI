# 行列演算に使用するライブラリを選ぶ
# numpy(use CPU) or cupy(use GPU)
# どちらを使うかは private.ini で設定

import importlib
import configparser
import logging

from debug import stream_hdl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(stream_hdl(logging.INFO))

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

    # load config
    config = configparser.ConfigParser()
    config.read('./src/private.ini', 'UTF-8')
    calculator = config.get('nn', 'calculator')

    if calculator == "GPU":
        logger.debug("matrix calculator -> GPU")
        return factory_cp()
    else:
        logger.debug("matrix calculator -> CPU")
        return factory_np()
