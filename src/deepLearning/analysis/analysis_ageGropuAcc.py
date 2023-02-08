# レースを推測する
# trainデータの正答率の分布を確認する目的
# 各年代でG1,2,3それぞれの正答率を積み上げ棒グラフで出力する
# 横軸:年
# 縦軸:割合(1つの棒グラフの意味- > G1的中数/G1レース数 + G2的中数/G2レース数 + G3的中数/G3レース数)

import pickle

from matplotlib import pyplot as plt
import xross
np = xross.facttory_xp()

import encoder

from iteration_utilities import deepflatten

from multi_layer_net_extend import MultiLayerNetExtend
from getFromDB              import db_race_list_id, db_race_grade
from deepLearning_common    import read_RaceInfo, prob_win
from file_path_mgr          import path_ini
from predictClass           import predict_XTbl

# ==========================================================================

if __name__ == "__main__":
    # パス読み込み
    path_tmp          = path_ini('common', 'path_tmp')
    path_trainedParam = path_ini('nn', 'path_trainedParam')

    # 学習済みネットワーク読み込み
    with open(path_trainedParam + "network.pickle", 'rb') as f:
        network: MultiLayerNetExtend = pickle.load(f)

    # ======================================================================

    start_year = 1986
    end_year = 2020
    race_id_list = db_race_list_id(start_year, end_year, -1)

    ans_hist = {}
    ans_sum  = {}
    for year in range(start_year, end_year + 1):
        ans_hist[str(year)] = {"G1":0, "G2":0, "G3":0}
        ans_sum[str(year)] = {"G1":0, "G2":0, "G3":0}

    # ======================================================================

    for race_id in race_id_list:
        # 推測するレースを設定する
        tmp_param = read_RaceInfo(str(race_id)) # race_id 指定(データベースから)
        # tmp_param = read_RaceInfo() # 当日推測用(pickleファイルから)
        # print("predict race_id = ", tmp_param.race_id)
        # print("year = ", race_id[0:4])
        #     芝 G1: 1, G2: 2, G3: 3, 無印(OP): 4
        #     ダ G1: 6, G2: 7, G3: 8, 無印(OP): 9
        grade = db_race_grade(str(race_id))
        if grade == 1 or grade == 6:
            grade = "G1"
        elif grade == 2 or grade == 7:
            grade = "G2"
        elif grade == 3 or grade == 8:
            grade = "G3"

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
        ans = encoder.Encoder_RankOneHot.RankOneHotClass()
        ans.set(race_id)
        ans.adj()
        for i in range(len(ans.xList)):
            if ans.xList[i] == 1:
                if predict_y[0] == i:
                    ans_hist[race_id[0:4]][grade] += 1
        ans_sum[race_id[0:4]][grade] += 1

    print("ans_hist", ans_hist)
    print("ans_sum", ans_sum)

    # 各年代のヒット率(ヒット数/レース数)
    percent_list_G1 = []
    percent_list_G2 = []
    percent_list_G3 = []
    for key in ans_hist.keys():
        percent_list_G1.append(ans_hist[key]["G1"] / ans_sum[key]["G1"])
        percent_list_G2.append(ans_hist[key]["G2"] / ans_sum[key]["G2"])
        percent_list_G3.append(ans_hist[key]["G3"] / ans_sum[key]["G3"])

    fig, ax = plt.subplots()
    
    ax.set_title("ACC")
    # 積み上げ棒グラフ
    G1 = ax.bar(ans_hist.keys(), percent_list_G1, label = "G1")
    G2 = ax.bar(ans_hist.keys(), percent_list_G2, label = "G2", bottom=percent_list_G1)
    G3 = ax.bar(ans_hist.keys(), percent_list_G3, label = "G3", bottom=[x + y for (x, y) in zip(percent_list_G1, percent_list_G2)])
    ax.legend()
    # 数値表示
    # !! matplot ver>=3.4
    ax.bar_label(G1, label_type="center")
    ax.bar_label(G2, label_type="center")
    ax.bar_label(G3, label_type="center")
    plt.show()
