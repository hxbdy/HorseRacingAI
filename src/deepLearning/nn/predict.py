# レースを推測する

import pickle
import xross
np = xross.facttory_xp()

from iteration_utilities import deepflatten

from multi_layer_net_extend import MultiLayerNetExtend
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

    # 推測するレースを設定する
    # tmp_param = read_RaceInfo('202206050811') # race_id 指定(データベースから)
    tmp_param = read_RaceInfo() # 当日推測用(pickleファイルから)
    print("predict race_id = ", tmp_param.race_id)

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
    print("x.shape = ", x.shape)

    # 推測
    y = list(deepflatten(network.predict(x)))
    prob_win(y)
