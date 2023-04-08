# 賭け方別の正答率を求める

import numpy as np

# TODO: ボックス買い時の正答率を求めてみたい

class Bet:
    @classmethod
    def win(cls, y:np, t:np):
        """単勝
        1位を予想する賭け方"""
        y = np.argmax(y, axis=1)
        if t.ndim != 1 : t = np.argmax(t, axis=1)
        accuracy = np.sum(y == t) / float(t.shape[0])
        return accuracy

    @classmethod
    def quinella(cls, y:np, t:np):
        """馬連
        1位、2位の組み合わせを予想する賭け方。着順は問わない"""

        # 昇順ソート済みインデックスのリストを作成
        y = y.argsort(axis=1)
        t = t.argsort(axis=1)

        # print("predict y[0] = ", y[0])
        # print("        t[0] = ", t[0])

        # 1位、2位のインデックスをTrueとする
        y_index = np.where((y==17) | (y==16), True, False)
        t_index = np.where((t==17) | (t==16), True, False)
        
        # ANDをとってTrueが2つあるならTrueとする
        cnt_hit      = y_index & t_index
        cnt_hit_bool = np.sum(cnt_hit, axis=1) == 2

        # print("hit?        = ", cnt_hit_bool)

        # Trueの数を数える
        accuracy = np.sum(cnt_hit_bool) / float(t.shape[0])

        return accuracy
    
    @classmethod
    def win_box3(cls, y:np, t:np):
        """単勝ボックス
        単勝を3頭買う。大体の場合赤字となる。"""

        # 昇順ソート済みインデックスのリストを作成
        y = y.argsort(axis=1)
        t = t.argsort(axis=1)

        # print("predict y[0] = ", y[0])
        # print("        t[0] = ", t[0])

        # 1位、2位、3位のインデックスをTrueとする
        y_index = np.where((y==17) | (y==16) | (y==15), True, False)
        t_index = np.where(t==17, True, False)
        
        # ANDをとってTrueが1つ以上あるならTrueとする
        cnt_hit      = y_index & t_index
        cnt_hit_bool = np.sum(cnt_hit, axis=1) >= 1

        # print("hit?        = ", cnt_hit_bool[0])

        # Trueの数を数える
        accuracy = np.sum(cnt_hit_bool) / float(t.shape[0])

        return accuracy
    