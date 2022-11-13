import logging
import logging.handlers
logger = logging.getLogger("XClass")


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

    def adj(self, log_queue):
        # ログハンドラ登録
        h = logging.handlers.QueueHandler(log_queue)
        root = logging.getLogger(self.__class__.__name__)
        root.addHandler(h)
        root.setLevel(logging.DEBUG)
        
        # 各関数で self.xList を更新する
        self.get()
        self.fix()
        self.pad()
        self.nrm()

        # TODO: 同じログが複数回出力されることがある
        root.debug("{0:23} {1} {2}".format(self.__class__.__name__, XClass.race_id, self.xList))
        
        return self.xList
