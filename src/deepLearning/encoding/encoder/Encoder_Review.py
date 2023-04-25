import numpy as np

from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from Encoder_X import XClass

class ReviewClass(XClass):

    def get(self):
        horse_id_list = self.nf.db_race_list_horse_id(self.race_id)
        self.xList = horse_id_list
    
    def fix(self):
        # レビューの値を馬ごとに持ってくる
        review_list = []
        for horse_id in self.xList:
            review = self.nf.db_horse_review(horse_id)
            review_list.append(review)
        self.xList = review_list

    def pad(self):
        pad_list = []
        pad_50 = (26.0, 58.0, 58.0, 26.0)
        pad_list.extend(pad_50 * 5)
        super().pad(pad_list)

    def nrm(self):
        np_xList = np.array(self.xList)

        # 各列最大値で割る方法
        # xList_max = np.max(np_xList, axis=0)
        # np_xList = np.divide(np_xList, xList_max, out = np.zeros_like(np_xList), where = (xList_max != 0))

        # zscoreを求める方法
        # 4つのパラメータがあるレビューが5個あるので、列数は20。
        np_xList = np_xList.reshape(-1, 20)
        np_xList = self.zscore(np_xList, axis=0)

        self.xList = np_xList.tolist()
