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

    def pad(self):
        pass

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

        root.info("{0:23} {1} {2}".format(self.__class__.__name__, XClass.race_id, self.xList))
        
        return self.xList
