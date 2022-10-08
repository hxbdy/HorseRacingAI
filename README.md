# HorseRacingAI

# Flow
|概要| 実行ファイル | 出力ファイル   |
| ---- | ---- |---- |
|1. [netkeiba.com](https://www.netkeiba.com/)　からレース情報と出走する馬の情報をスクレイピングする。|./src/scraping/scrapingUmaData.py	|./dst/scrapingResult/raceGradedb.pickle, racedb.pickle, horsedb.pickle|
|2. 1.で取得した情報を標準化する|./src/deepLearning/scrapingDataNrm.py|./dst/learningList/t.pickle, x.pickle|
|3. ディープラーニングで学習する|./src/deepLearning/deepLearningMain.py|./dst/trainedParam/gradientb1.txt, gradientb2.txt, gradientW1.txt, gradientW2.txt|
|4. 3.情報で推定する(未実装)|-| - |

# Setup

## conda env
* Python 3.8.13
* cuda 11.7.0
* cupy 8.3.0
* selenium 4.2.0

## conda installation
### app
1. [Anaconda | Anaconda Distribution](https://www.anaconda.com/products/distribution)
2. [CUDA Toolkit - Free Tools and Training | NVIDIA Developer](https://developer.nvidia.com/cuda-toolkit)

### package
1. [Cupy :: Anaconda.org](https://anaconda.org/anaconda/cupy)
2. [Selenium::Anaconda.org](https://anaconda.org/conda-forge/selenium)
3. [Webdriver Manager :: Anaconda.org](https://anaconda.org/conda-forge/webdriver-manager)
4. [Python Dateutil :: Anaconda.org](https://anaconda.org/conda-forge/python-dateutil)
5. [Sqlite3 :: Anaconda.org](https://anaconda.org/blaze/sqlite3)

## PATH
conda 仮想環境上で各フォルダへパスを通す作業が必要です。  
以下コマンドを仮想環境上で実行してパスを通してください。

```bash:
> conda env config vars set PYTHONPATH=\
src/common;\
src/deepLearning/encoding;\
src/deepLearning/nn;\
src/deepLearning/stdTime;\
src/deepLearning;\
src/sample;\
src/scraping;\
src;\
```

パスを追加できたかは以下コマンドで確認できます。
```bash:
> conda env config vars list
```

追加したパスを有効にするにはリアクティベートします。
```bash:
> conda deactivate
> conda activate HorseRacingAI 
```

内部的には追加したパスは以下ファイルで管理されています。
```bash:
"C:\Users\{YOUR USERNAME}\anaconda3\envs\{YOUR ENV NAME}\conda-meta\state"
```

# Untracked Folder / File

## private.ini
./src/private.ini を作成して以下を記入して保存してください。  
メールとパスワードはネット競馬にログインするために使用します。

```txt:whatprivate.ini
[scraping]
browser = Chrome or FireFox
mail = hogehoge@mail.com
pass = password
```
## resrc
./resrc/netkeiba フォルダ以下にnet.keibaから作成したデータベースを保存します。  

## dst
./dst/learningList フォルダ以下にデータベースから作成する学習用にエンコードされた学習用データをpickle形式で保存します  
./dst/trainedParam フォルダ以下にNNによって学習した行列パラメータを保存します  
./dst/output.log に直前に実行したプログラムのログを保存します

# 参考
- [クローリング&スクレイピング 競馬情報抜き出してみた - Qiita](https://qiita.com/penguinz222/items/6a30d026ede2e822e245)
- [海外競馬英和辞典　ＪＲＡ](https://www.jra.go.jp/keiba/overseas/yougo/index.html)
- [着差 (競馬) - Wikipedia](https://ja.wikipedia.org/wiki/%E7%9D%80%E5%B7%AE_(%E7%AB%B6%E9%A6%AC)#:~:text=%E7%AB%B6%E9%A6%AC%E3%81%AE%E7%AB%B6%E8%B5%B0%E3%81%AB%E3%81%8A%E3%81%91%E3%82%8B%E7%9D%80,%E7%AB%B6%E8%B5%B0%E3%81%A7%E3%81%AF%E7%94%A8%E3%81%84%E3%82%89%E3%82%8C%E3%81%AA%E3%81%84%E3%80%82)
