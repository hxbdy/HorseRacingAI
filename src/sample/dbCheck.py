# DB の一貫性(Consistency) を確認する

import pickle
import logging
import sys
import os

# commonフォルダ内読み込みのため
sys.path.append(os.path.abspath(".."))
parentDir = os.path.dirname(os.path.abspath(__file__))
if parentDir not in sys.path:
    sys.path.append(parentDir)

from deprecated.HorseDB import HorseDB
from deprecated.RaceDB import RaceDB

# debug initialize
# LEVEL : DEBUG < INFO < WARNING < ERROR < CRITICAL
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#logging.disable(logging.DEBUG)

# レース情報読み込み
with open("../../dst/scrapingResult/racedb.pickle", 'rb') as f:
        racedb = pickle.load(f)
    
# 馬情報読み込み
with open("../../dst/scrapingResult/horsedb.pickle", 'rb') as f:
        horsedb = pickle.load(f)

# 各要素のlenが同じことを確認する
flg = racedb.selfConsistencyCheck()
logger.debug(flg)

flg = horsedb.selfConsistencyCheck()
logger.debug(flg)
