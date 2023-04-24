CHCP 932

REM 当日レーススクレイピング + 推測 + 賭ける
REM !! ここで学習は行わない。学習は prepare.bat

REM scrape
python ./src/scraping/netkeiba_scraping2.py %1 %2 %3

REM predict
python ./src/deepLearning/nn/predict.py

REM bet
python ./src/scraping/autobet.py
