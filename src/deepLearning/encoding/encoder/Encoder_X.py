from log import *

import multiprocessing

import numpy as np

from NetkeibaDB_IF import NetkeibaDB_IF
from RaceInfo      import RaceInfo

class XClass:
    # 全インスタンス共通の変数
    race_id:str        = '0'
    pad_size:int       = 16
    race_info:RaceInfo = RaceInfo()
    
    # 自身が子プロセスか判断するために使う
    is_child:bool      = False

    def __init__(self):
        self.xList = []
        self.nf:NetkeibaDB_IF = NetkeibaDB_IF("RAM", read_only=True)

        if XClass.is_child:
            self.logger = multiprocessing.get_logger()
            self.logger.setLevel(logging.WARNING)
        else:
            self.logger = logging.getLogger(self.__class__.__name__)
            self.logger.setLevel(logging.INFO)
        
    def set(self, target_race_id):
        XClass.race_id = target_race_id

    def get(self):
        pass

    def fix(self):
        pass

    def pad(self, obj = 0):
        # リスト拡張 デフォルトではゼロで埋める
        adj_size = abs(XClass.pad_size - len(self.xList))

        if len(self.xList) < XClass.pad_size:
            # 要素を増やす
            # ダミーデータ：0を追加．
            for i in range(adj_size):
                self.xList.append(obj)
        else:
            # 要素を減らす
            for i in range(adj_size):
                del self.xList[-1]

    def nrm(self):
        pass

    def adj(self):        
        # 各関数で self.xList を更新する
        self.get()
        self.fix()
        self.pad()
        self.nrm()
        return self.xList
    
    # =======================
    # = util functions      =
    # =======================
    
    def zscore(self, x, axis = None, reverse = False):
        """平均が0, 標準偏差が1になるように変換した得点

        Parameters
        ----------
        x : numpy or list
            計算対象。32bit floatに変換して計算する
        axis : int
            計算方向。2Dの場合、0は列、1は行方向
        reverse : bool
            全ての値にマイナスをかけて、大小関係を反転させてから計算する
            1位の値が一番小さいときに使う

        Returns
        -------
        zscore : numpy
            変換後の値
        """

        # numpyに変換して行う
        x_float32 = np.array(x, copy=True, dtype=np.float32)

        if reverse:
            x_float32 = -x_float32
        xmean = x_float32.mean(axis=axis, keepdims=True)
        xstd = np.std(x_float32, axis=axis, keepdims=True)
        zscore = np.divide((x_float32 - xmean), xstd, out = np.zeros_like(x_float32), where = (xstd != 0))
        return zscore
