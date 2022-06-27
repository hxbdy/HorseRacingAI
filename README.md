# HorseRacingAI

やるぞ～～  
2022年有馬記念に間に合わせたい。

## 競走馬データスクレイピング
持ってくるデータ

| 変数名 |  内容  |
| ---- | ---- |
|    |日付	|
|    |開催	|
|    |天気|
|    |R|
|    |頭数|
|    |枠番|
|    |馬番|
|    |オッズ|
|    |人気|
|    |着順|
|    |騎手|
|    |斤量|
|    |距離|
|    |馬場|
|    |タイム|
|    |着差|
|    |勝ち馬(2着馬)|
|    |賞金|
||XXX|

## 入力データX
| 変数名 |  内容  |
| ---- | ---- |
|    |日付	|
|    |開催	|
|    |天気|
|    |R|
|    |頭数|
|    |枠番|
|    |馬番|
|    |オッズ|
|    |人気|
|    |騎手|
|    |斤量|
|    |距離|
|    |馬場|
|    |賞金総額|
||パパ因子|
||ママ因子|

## パパ、ママ因子継承について
獲得賞金、勝率とか計算する

## 教師データ
2020年までのデータで学習する。
2021年のデータで推論する。

## 環境
* Python 3.9.12
* cuda 11.7.0
* cupy 8.3.0

## installation
1. [Anaconda | Anaconda Distribution](https://www.anaconda.com/products/distribution)
2. [CUDA Toolkit - Free Tools and Training | NVIDIA Developer](https://developer.nvidia.com/cuda-toolkit)
3. [Cupy :: Anaconda.org](https://anaconda.org/anaconda/cupy)


## 参考
[クローリング&スクレイピング 競馬情報抜き出してみた - Qiita](https://qiita.com/penguinz222/items/6a30d026ede2e822e245)
