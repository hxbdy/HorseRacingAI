
REM scrape
python ./src/scraping/netkeiba_scraping2.py %1 %2

REM predict
python ./src/deepLearning/nn/predict.py
