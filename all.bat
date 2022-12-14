REM update DB
REM ###

REM scrape
python ./src/scraping/netkeiba_scraping.py %1 %2

REM normalize
REM ###

REM deep learning
REM ###

REM predict
python ./src/deepLearning/nn/predict.py

REM clean
DEL /F ".\dst\tmp.pickle"

pause
