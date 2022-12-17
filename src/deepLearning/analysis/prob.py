import numpy as np

def prob_win(value_list):
    # 勝つ可能性 (ロジットモデル)
    ls = np.array(value_list)
    ls_sorted_idx = np.argsort(-ls) # 降順のソート
    ls_sorted = ls[ls_sorted_idx]
    prob = np.exp(ls_sorted)/sum(np.exp(ls_sorted)) # 確率計算
    prob_disp = ["{:.3f}".format(i) for i in prob] # 表示桁数を制限
    
    print(["{:^5d}".format(i) for i in ls_sorted_idx+1])
    print(prob_disp)
    #return list(ls_sorted_idx), prob
