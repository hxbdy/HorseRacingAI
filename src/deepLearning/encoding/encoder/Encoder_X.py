from debug import stream_hdl, file_hdl
import logging
import numpy as np

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("output"))

class XClass:
    # 全インスタンス共通の変数
    race_id = '0'

    pad_size = 18

    def __init__(self):
        self.xList = []
        
    def set(self, target_race_id):
        XClass.race_id = target_race_id

    def get(self):
        if XClass.race_id == '0':
            logger.critical("race_id == 0 !!")

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
        if (np.max(self.xList) > 1.1) or (np.min(self.xList) < -0.1):
            logger.debug("CHECK encoded value !! , max = {0:4.2f}, min = {1:4.2f}, encoder = {2}".format(np.max(self.xList), np.min(self.xList), self.__class__))
        return self.xList
