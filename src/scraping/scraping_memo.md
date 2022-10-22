# About
1984年にグレード制(G1やG2など)が導入された。
理由は不明だが、netkeibaでは1986年以降のレースにグレード表示がされており、1985年までは全てOP扱いになっている。
よってデータを集めるのを簡略化するため、とりあえず、1986年以降の重賞レースに出場した馬のみのデータを収集する。


# スクレイピングの流れ
1. https://db.netkeiba.com/?pid=race_search_detail で、レース検索し、レースIDを得る。
2. https://db.netkeiba.com/race/<<raceID>> <<raceID>>に1)で取得したレースIDを入れて、レース情報と出走馬のIDを得る。
3. https://db.netkeiba.com/horse/<<horseID>> <<horseID>>に2)で取得したホースIDを入れて、馬の情報を得る。

# private.iniについて
srcフォルダ直下に private.ini を作成して以下を記入して保存してください。
メールとパスワードはネット競馬にログインするために使用します。  
**まちがってもパスワードを入力したprivate.iniをプッシュしないこと**

```txt:whatprivate.ini
[scraping]
browser = Chrome or FireFox
mail = hogehoge@mail.com
pass = password
```

# 環境
- Python 3.8.3
- selenium 4.2.0
- geckodriver 0.31.0
- Firefox 102.0


# memo
driverをヘッドレスモードで起動すると、画面を表示させずに処理する。

```python:how2headlessmode.py
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(DriverPath, options = options)
```

webdriver_managerにより自動的にドライバがダウンロードされる．
初回ダウンロード時にprocell unexpectedly closedエラーが出るが再実行すると発生しなくなる．
