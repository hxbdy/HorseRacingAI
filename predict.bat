CHCP 932

REM �������[�X�X�N���C�s���O + ���� + �q����
REM !! �����Ŋw�K�͍s��Ȃ��B�w�K�� prepare.bat

REM scrape
python ./src/scraping/netkeiba_scraping2.py %1 %2 %3

REM predict
python ./src/deepLearning/nn/predict.py

REM bet
python ./src/scraping/autobet.py
