import logging
logger = logging.getLogger(__name__)

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
        None

    def pad(self):
        None

    def nrm(self):
        None

    def adj(self):
        # 各関数で self.xList を更新する
        self.get()
        self.fix()
        self.pad()
        self.nrm()
        return self.xList
