# 賭け方別の正答率を求める

import numpy as np

def numpy_isin(a, b):
    """1D/2D用isin()
    a が b に含まれているかを True/Falseでaの形状を保持して返す
    ex) a = [[1, 2, 3], [...]]
        b = [[4, 1, 2], [...]]
        -> return [[True, True, False], [...]]
    """
    if a.ndim == 2:
        return (a[:, None, :, None] == b[:, None, None]).any(-1).reshape(-1, a.shape[1])
    elif a.ndim == 1:
        return np.isin(a, b)
    else:
        return None


class Bet:
    @classmethod
    def win(cls, y:np, t:np):
        """単勝
        1位を予想する賭け方"""
        
        accuracy = 0
        if t.ndim == 1:
            t = np.argmax(t)
            y = np.argmax(y)
            if y == t:
                accuracy = 1
            else:
                accuracy = 0
            
        elif t.ndim == 2:
            t = np.argmax(t, axis=1)
            y = np.argmax(y, axis=1)
            accuracy = np.sum(y == t) / float(t.shape[0])

        return accuracy

    @classmethod
    def quinella(cls, y:np, t:np):
        """馬連
        1位、2位の組み合わせを予想する賭け方。着順は問わない"""

        # 昇順ソート済みインデックスのリストを作成
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

        # Trueの数を数える
        accuracy = cnt_hit / float(t.shape[0])

        return accuracy
    
    @classmethod
    def win_box3(cls, y:np, t:np):
        """単勝ボックス
        単勝を3頭買う。大体の場合赤字"""

        # 昇順ソート済みインデックスのリストを作成
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

        # Trueの数を数える
        accuracy = cnt_hit / float(t.shape[0])

        return accuracy
    
    @classmethod
    def win_box2(cls, y:np, t:np):
        """単勝ボックス
        単勝を2頭買う。おそらく赤字"""

        # 昇順ソート済みインデックスのリストを作成
        sort_y = y.copy()
        sort_y = sort_y.argsort(axis=1)

        # 各データの1～3位のリスト 
        sort_y_1st = sort_y[:, -1]
        sort_y_2nd = sort_y[:, -2]
        # sort_y_3rd = sort_y[:, -3]

        sort_t = t.copy()
        sort_t = sort_t.argsort(axis=1)

        sort_t_1st = sort_t[:, -1]
        # sort_t_2nd = sort_t[:, -2]
        # sort_t_3rd = sort_t[:, -3]
        
        # 予想の1位～2位と正解の1位を比較、
        cnt_hit = np.sum(sort_y_1st == sort_t_1st) + np.sum(sort_y_2nd == sort_t_1st)

        # Trueの数を数える
        accuracy = cnt_hit / float(t.shape[0])

        return accuracy
    
    @classmethod
    def quinella_place(cls, y:np, t:np):
        """ワイド
        3着以内に入る2頭を選ぶ"""        
        
        # 2位までの予想
        sort_y = y.copy()
        sort_y = sort_y.argsort(axis=1)
        sort_y = sort_y[:, -2:]

        # 3位までの正解
        sort_t = t.copy()
        sort_t = sort_t.argsort(axis=1)
        sort_t = sort_t[:, -3:]

        # y が t に含まれている数を計上
        isin = numpy_isin(sort_y, sort_t)
        # print("isin?        = ", isin[0])

        isin_sum = np.sum(isin, axis=1)
        # 2頭以上の予想が含まれている
        cnt_hit = np.sum(isin_sum >= 2)
        
        accuracy = cnt_hit / float(t.shape[0])

        return accuracy

    @classmethod
    def quinella_place_box3(cls, y:np, t:np):
        """ワイド
        3着以内に入る2頭を選ぶ
        3頭でボックス買いした場合の正答率"""

        sort_y = y.copy()
        sort_t = t.copy()

        # 昇順ソート
        sort_y = sort_y.argsort(axis=-1)
        sort_t = sort_t.argsort(axis=-1)

        # 先頭3頭の情報のみにする
        if sort_y.ndim == 1:
            sort_y = sort_y[-3:]
            sort_t = sort_t[-3:]
        elif sort_y.ndim == 2:
            sort_y = sort_y[:, -3:]
            sort_t = sort_t[:, -3:]

        # print("sort_y = ", sort_y)
        # print("sort_t = ", sort_t)

        # y が t に含まれている数を計上
        isin = numpy_isin(sort_y, sort_t)
        # print("isin?        = ", isin)

        isin_sum = np.sum(isin, axis=-1)
        # 2頭以上の予想が含まれている
        cnt_hit = np.sum(isin_sum >= 2)
        
        if sort_y.ndim == 1:
            accuracy = cnt_hit
        elif sort_y.ndim == 2:       
            accuracy = cnt_hit / float(sort_t.shape[0])

        return accuracy
