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
        # print("hit?        = ", np.sum(y == t))
        accuracy = np.sum(y == t) / float(t.shape[0])
        return accuracy

    @classmethod
    def quinella(cls, y:np, t:np):
        """馬連
        1位、2位の組み合わせを予想する賭け方。着順は問わない"""

        # 昇順ソート済みインデックスのリストを作成
        # print("predict y[0] = ", y[0])
        # print("        t[0] = ", t[0])
        
        sort_y = y.copy()
        sort_y = sort_y.argsort(axis=1)

        # 各データの1～3位のリスト 
        sort_y_1st = sort_y[:, -1]
        sort_y_2nd = sort_y[:, -2]
        # sort_y_3rd = sort_y[:, -3]

        sort_t = t.copy()
        sort_t = sort_t.argsort(axis=1)

        sort_t_1st = sort_t[:, -1]
        sort_t_2nd = sort_t[:, -2]
        # sort_t_3rd = sort_t[:, -3]
        
        # ヒット数 = 
        # (予想1位 == 正解1位) かつ (予想2位 == 正解2位) +
        # (予想1位 == 正解2位) かつ (予想2位 == 正解1位)
        cnt_hit = np.sum(sort_y_1st == sort_t_1st) + np.sum(sort_y_2nd == sort_t_2nd) + \
                  np.sum(sort_y_1st == sort_t_2nd) + np.sum(sort_y_2nd == sort_t_1st)
        # print("hit?        = ", cnt_hit)

        # Trueの数を数える
        accuracy = cnt_hit / float(t.shape[0])

        return accuracy
    
    @classmethod
    def win_box3(cls, y:np, t:np):
        """単勝ボックス
        単勝を3頭買う。大体の場合赤字"""

        # 昇順ソート済みインデックスのリストを作成
        # print("predict y[0] = ", y[0])
        # print("        t[0] = ", t[0])
        
        sort_y = y.copy()
        sort_y = sort_y.argsort(axis=1)

        # 各データの1～3位のリスト 
        sort_y_1st = sort_y[:, -1]
        sort_y_2nd = sort_y[:, -2]
        sort_y_3rd = sort_y[:, -3]

        sort_t = t.copy()
        sort_t = sort_t.argsort(axis=1)

        sort_t_1st = sort_t[:, -1]
        # sort_t_2nd = sort_t[:, -2]
        # sort_t_3rd = sort_t[:, -3]
        
        # 予想の1位～3位と正解の1位を比較、
        cnt_hit = np.sum(sort_y_1st == sort_t_1st) + np.sum(sort_y_2nd == sort_t_1st) + np.sum(sort_y_3rd == sort_t_1st)
        # print("hit?        = ", cnt_hit)

        # Trueの数を数える
        accuracy = cnt_hit / float(t.shape[0])

        return accuracy
    