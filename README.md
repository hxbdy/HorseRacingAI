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

## コーディングルール
1. 関数 : camel notation (ex: sampleFunc())
2. クラス : upper camel case (ex: SampleClass())
3. 変数 : snake case (ex: sample_tmp)

## 学習済みパラメータについて
main.pyで学習するとtrainedParamフォルダ以下に学習済みパラメータを保存する。  
学習済みパラメータを使った推論を行う場合、これらをロードする。  

## caonda env
* Python 3.8.13
* cuda 11.7.0
* cupy 8.3.0
* selenium 4.2.0


## conda installation
1. [Anaconda | Anaconda Distribution](https://www.anaconda.com/products/distribution)
2. [CUDA Toolkit - Free Tools and Training | NVIDIA Developer](https://developer.nvidia.com/cuda-toolkit)
3. [Cupy :: Anaconda.org](https://anaconda.org/anaconda/cupy)
4. [Selenium::Anaconda.org](https://anaconda.org/conda-forge/selenium)
5. [Webdriver Manager :: Anaconda.org](https://anaconda.org/conda-forge/webdriver-manager)
6. [Python Dateutil :: Anaconda.org](https://anaconda.org/conda-forge/python-dateutil)

## 参考
[クローリング&スクレイピング 競馬情報抜き出してみた - Qiita](https://qiita.com/penguinz222/items/6a30d026ede2e822e245)
[海外競馬英和辞典　ＪＲＡ](https://www.jra.go.jp/keiba/overseas/yougo/index.html)