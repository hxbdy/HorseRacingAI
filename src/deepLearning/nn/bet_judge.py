# 賭けるべきか判断する

import numpy as np

class BetJudge:
    @classmethod
    def rankonehot(cls, prob:np) -> bool:
        """正解ラベルをRankOneHotClassとして学習したときの賭けるべきしきい値
        1位の確率が一定値以上なら買う"""
        return prob[0] > 0.7
    
    @classmethod
    def time(cls, prob:np) -> bool:
        """正解ラベルをTimeClassとして学習したときの賭けるべきしきい値
        1位と2位の差が一定以上なら買う"""
        return (prob[0] - prob[1]) > 0.15
    