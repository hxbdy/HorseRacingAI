# ネットワークの正答率の分布を確認する
# 正解したレース、不正解だったレースを確認できるSQLファイルを生成する

import pickle
import os

from iteration_utilities import deepflatten

import encoder
from NetkeibaDB_IF          import NetkeibaDB_IF
from multi_layer_net_extend import MultiLayerNetExtend
from deepLearning_common    import read_RaceInfo, prob_win
from file_path_mgr          import path_ini
from predictClass           import predict_XTbl
from table                  import tTbl

from bet                    import Bet

import xross
np = xross.facttory_xp()

# ==========================================================================

if __name__ == "__main__":
    # パス読み込み
    path_tmp          = path_ini('common', 'path_tmp')
    path_trainedParam = path_ini('nn', 'path_trainedParam')

    # 学習済みネットワーク読み込み
    with open(path_trainedParam + "network.pickle", 'rb') as f:
        network: MultiLayerNetExtend = pickle.load(f)

    # ======================================================================
    nf = NetkeibaDB_IF("RAM")

    start_year = 1986
    end_year = 2020
    race_id_list = nf.db_race_list_id(start_year, end_year, -1)
    hit = []
    miss = []
    # ======================================================================

    for race_id in race_id_list:
        # 推測するレースを設定する
        tmp_param = read_RaceInfo(str(race_id)) # race_id 指定(データベースから)
        # ======================================================================
    
        # 推測用エンコード
        x = []
        for func in predict_XTbl:
            # インスタンス生成
            predict = func()
            # レース情報設定
            predict.race_info = tmp_param
            # エンコード
            x.append(predict.adj())
        x = np.array(list(deepflatten(x))).reshape(1, -1)

        # ======================================================================

        # 推測
        y = list(deepflatten(network.predict(x)))
        predict_y = prob_win(y)

        # 正解ラベル取り出し
        # 正解用テーブルtTblに入っているのを持ってくる
        ans = tTbl[0]()
        ans.set(race_id)
        ans.adj()

        acc = Bet.quinella_place_box3(np.array(y), np.array(ans.xList))

        if int(acc) == 1:
            hit.append(race_id)
        else:
            miss.append(race_id)

        print("acc = {0}".format(len(hit) / len(race_id_list)))

    # 予測したrace_idの的中/非的中を確認するためのSQL作成
    os.makedirs("./dst/analysis", exist_ok=True)
    with open("./dst/analysis/hit.sql", 'w') as f:
        hit_race_id = " OR ".join(map(lambda x: 'race_id="{0}"'.format(x), hit))
        hit_race_id = "SELECT * FROM race_info WHERE " + hit_race_id + ";"
        f.write(hit_race_id)
    with open("./dst/analysis/miss.sql", 'w') as f:
        miss_race_id = " OR ".join(map(lambda x: 'race_id="{0}"'.format(x), miss))
        miss_race_id = "SELECT * FROM race_info WHERE " + miss_race_id + ";"
        f.write(miss_race_id)
