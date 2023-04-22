# HorseRacingAI

# Flow
| About | Exe | Output |
| ----  | --- | ------ |
|1. [netkeiba.com](https://www.netkeiba.com/)から必要情報をスクレイピングする|src\scraping\netkeiba_scraping.py	|resrc\netkeibaDB\netkeiba.db|
|2. 1.で取得した情報をエンコードする|src\deepLearning\encoding\encodingMain.py|dst\learningList\newest|
|3. ディープラーニングで学習する|src\deepLearning\nn\deepLearningMain.py|dst\trainedParam\newest|
|4. 3.情報で推定する|src\deepLearning\nn\predict.py| - |

# Setup

## conda env
| About | Ver |
| ----       | ---    |
| Python     | 3.8.13 |
| cuda       | 11.7.0 |
| cupy       | 8.3.0 |
| selenium   | 4.2.0 |
| sqlite3    | 3.8.6 |
| matplotlib | 3.6.2 |
| pandas     | 1.5.2 |
| psutil     | 5.9.1 |

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
6. [Matplotlib :: Anaconda.org](https://anaconda.org/conda-forge/matplotlib)
7. [Iteration Utilities :: Anaconda.org](https://anaconda.org/conda-forge/iteration_utilities)
8. [Pandas :: Anaconda.org](https://anaconda.org/anaconda/pandas)
9. [Psutil :: Anaconda.org](https://anaconda.org/conda-forge/psutil)
10. [Py Cord :: Anaconda.org](https://anaconda.org/conda-forge/py-cord)

## PATH
conda 仮想環境上で各フォルダへパスを通す作業が必要です。  
以下コマンドを仮想環境上で実行してパスを通してください。

```bash:
> conda env config vars set PYTHONPATH=\
src/deepLearning/encoding/encoder;\
src/deepLearning/analysis;\
src/deepLearning/encoding;\
src/deepLearning/nn;\
src/deepLearning;\
src/common;\
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
> conda activate {YOUR ENV NAME}
```

内部的には追加したパスは以下ファイルで管理されています。
```bash:
"C:\Users\{YOUR USERNAME}\anaconda3\envs\{YOUR ENV NAME}\conda-meta\state"
```

# Untracked Dir / File

## private.ini
./src/private.ini を作成して以下を記入して保存してください。  
- scrapingカテゴリ  
メールとパスワードはネット競馬にログインするために使用します。
- discordカテゴリ  
discordのbotを用意するとチャットを通じてコードを実行することができます。
- jraカテゴリ  
学習結果を用いて自動投票するために必要です。

```txt:whatprivate.ini
[scraping]
browser = Chrome or FireFox
mail = 
pass = 
process_num = 

[nn]
# 行列演算ハード指定 GPU or CPU
calculator = 

[discord]
DISCORD_SERVER_ID = 
TOKEN = 

[jra]
INET_ID = 
MEMBER_ID = 
P_ARS_ID = 
PASS = 

```
## resrc
net.keiba から作成したデータベースを resrc\netkeibaDB\netkeiba.db に保存します  

## dst
|Dir|About|
| ---- | ---- |
|dst\learningList\newest|データベースから作成する学習用にエンコードされた学習用データをpickle形式で保存します|
|dst\trainedParam\newest|NNによって学習した行列パラメータを保存します|
|dst\output.log|直前に実行したプログラムのログを保存します|

# About DB
 * エンコード高速化のため、以下の事をしています。
## LOCATE
* DBをROM実行、RAM実行の2種類で使い分けています。
### ROM exe
* DBの更新時はROM実行します。RAM実行するとDBへの変更がセーブされないためです。

### RAM exe
* エンコード時はRAM実行します。
* ただし、プロセス毎にDRAMへ展開するため、(DBの容量 * エンコード数) 分のメモリを必要とします。
* 2023/03/11 現在 約 4 [GB] 消費します。
* ROM実行することも可能です。XClass.__ init __() を確認してください。

## SCHEMA
* DB初期化時、1度だけインデックスを自動で貼ります。
* インデックスを追加できたかは以下コマンドで確認できます。
```bash:
sqlite> .indices
race_info_grade
race_result_grade
race_result_race_data2
```

# 参考
- [クローリング&スクレイピング 競馬情報抜き出してみた - Qiita](https://qiita.com/penguinz222/items/6a30d026ede2e822e245)
- [海外競馬英和辞典　ＪＲＡ](https://www.jra.go.jp/keiba/overseas/yougo/index.html)
- [着差 (競馬) - Wikipedia](https://ja.wikipedia.org/wiki/%E7%9D%80%E5%B7%AE_(%E7%AB%B6%E9%A6%AC)#:~:text=%E7%AB%B6%E9%A6%AC%E3%81%AE%E7%AB%B6%E8%B5%B0%E3%81%AB%E3%81%8A%E3%81%91%E3%82%8B%E7%9D%80,%E7%AB%B6%E8%B5%B0%E3%81%A7%E3%81%AF%E7%94%A8%E3%81%84%E3%82%89%E3%82%8C%E3%81%AA%E3%81%84%E3%80%82)
