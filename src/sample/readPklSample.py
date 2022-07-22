import pickle

with open('../../result/race/198601010809.pickle', 'rb') as f:
    data = pickle.load(f)

print(data)

# レースごとに入力する
# 1レースのpklロード
#  - HorseID参照、展開
# 正規化(ここが一番たいへん)
#  - 足りないデータをダミーデータで埋める
#  - 古いデータの影響度係数をかけてみたりするのもここ
