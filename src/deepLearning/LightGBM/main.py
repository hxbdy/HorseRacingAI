import numpy as np
import pandas as pd
import sqlite3

import lightgbm as lgb

from deepLearning_common    import encoding_load
from file_path_mgr          import path_ini
from util                   import shuffle_dataset


path_learningList = path_ini('nn', 'path_learningList')
path_netkeibaDB   = path_ini('common', 'path_netkeibaDB')

x_data, t_data = encoding_load(path_learningList)

con = sqlite3.connect(path_netkeibaDB)

# TODO:
# race_result(result列を除く) <- race_info, horse_prof を結合
# rssult 列を正解として取り出す
# ラベル列は明示的に示して学習してみる
# LightGBMのCategorical Featureによって精度が向上するか？ - Qiita
# https://qiita.com/sinchir0/items/b038757e578b790ec96a#%E5%88%9D%E3%82%81%E3%81%AB
# df  = pd.read_sql_query('SELECT * FROM race_info LIMIT 10', con)
# print(df)
# exit(-1)

print(x_data.shape)
print(t_data.shape)

# データシャッフル
rate = 0.8
train_num = int(x_data.shape[0] * rate)
x_data, t_data = shuffle_dataset(x_data, t_data)
x_train = x_data[:train_num]
t_train = np.argmax(t_data[:train_num], axis=1)
x_test = x_data[train_num:]
t_test = np.argmax(t_data[train_num:], axis=1)

# print(x_train[0,0:20])
# print(t_train[0])
# exit(-1)

# LGBM init
params = {
    'task': 'train',
    'boosting_type': 'gbdt',
    'objective': 'multiclass',
    'num_class': 12,
    'verbose': 2,
    'num_leaves': 300,
    'learning_rate': 0.01,
    'random_seed': 1,
    'max_depth': 2,
    'num_boost_round': 1000,
    'early_stopping_rounds': 10,
}


train_data = lgb.Dataset(x_train, label=t_train)
eval_data  = lgb.Dataset(x_test, label=t_test, reference=train_data)

gbm = lgb.train(
    params=params,
    train_set=train_data,
    valid_sets=eval_data,
    num_boost_round=100,
    verbose_eval=5,
)

