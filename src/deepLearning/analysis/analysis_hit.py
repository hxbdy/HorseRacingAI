# ネットワークの正答率の分布を確認する
# 正解したレース、不正解だったレースを確認できるテーブルをDBに生成する
from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
from rich.progress import track

import pickle
import os

from iteration_utilities import deepflatten

from NetkeibaDB_IF          import NetkeibaDB_IF
from multi_layer_net_extend import MultiLayerNetExtend
from deepLearning_common    import read_RaceInfo, prob_win
from file_path_mgr          import path_ini
from predictClass           import predict_XTbl
from table                  import tTbl

from bet                    import Bet
from bet_judge              import BetJudge

import xross
np = xross.facttory_xp()

# ==========================================================================

# TODO:賭けるべきかの検討メモ
# 2022年を除いたデータでエンコード、学習
# 2022年のデータをここで取得して正答率を調べる
# 正解とする賭け方は一度確認する(最初は単勝で確認するべき。)
# probを確認して賭けるしきい値を確認する

if __name__ == "__main__":
    # パス読み込み
    path_tmp          = path_ini('common', 'path_tmp')
    path_trainedParam = path_ini('nn', 'path_trainedParam')

    # 学習済みネットワーク読み込み
    with open(path_trainedParam + "network.pickle", 'rb') as f:
        network: MultiLayerNetExtend = pickle.load(f)

    # ======================================================================
    nf = NetkeibaDB_IF("ROM", read_only=False)

    start_year = 2023
    end_year = 2023
    race_id_list = nf.db_race_list_id(start_year, end_year, -1)
    hit = []
    miss = []
    probs_hit = {}
    probs_miss = {}
    bet_cnt = 0 # 賭けたレース数
    # ======================================================================

    for race_id in track(race_id_list, description="Predict..."):
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
        predict_y, prob = prob_win(y)

        if BetJudge.rankonehot(prob):
            # 正解ラベル取り出し
            # 正解用テーブルtTblに入っているのを持ってくる
            ans = tTbl[0]()
            ans.set(race_id)
            ans.adj()
            acc = Bet.win(np.array(y), np.array(ans.xList))
        else:
            continue
        bet_cnt += 1

        if int(acc) == 1:
            hit.append(race_id)
            probs_hit[race_id] = prob
        else:
            miss.append(race_id)
            probs_miss[race_id] = prob

        logger.info("acc = {0}".format(len(hit) / bet_cnt))

    # 予測したrace_idの的中/非的中を確認するためのSQL作成
    nf.db_race_make_debug_table("hit", hit)
    nf.db_race_make_debug_table("miss", miss)

    # 正解、不正解のprobを書き込む
    os.makedirs('./dst/analysis', exist_ok=True)
    with open('./dst/analysis/probs_hit.txt','w') as f:
        for key, value in probs_hit.items():
            f.writelines(f"{key}:{value}\n")

    with open('./dst/analysis/probs_miss.txt','w') as f:
        for key, value in probs_miss.items():
            f.writelines(f"{key}:{value}\n")
