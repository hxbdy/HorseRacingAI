import pickle
import os
import sys
from pathlib import Path
import logging

# commonフォルダ内読み込みのため
sys.path.append(os.path.abspath(".."))
parentDir = os.path.dirname(os.path.abspath(__file__))
if parentDir not in sys.path:
    sys.path.append(parentDir)

# ENUM horse_data
# horse_data = [horseID, prof_contents, blood_list, perform_contents, check]
# '1982101018'
# ['1982年4月22日', '00340', '辻幸雄', '谷岡正次', '静内町', '-', '1億330万円 (中央)', '15戦8勝 [8-3-1-3]', "86'札幌記念(G3)", 'ダンツウイッチ、フォースタテヤマ']
# ['000a000b7f', '000a0009ab', '000a0035a9', '1975104765', '000a000416', '1955100859']
# [['1987/06/14', '198701010209', '13', '1', '1', '1.4', '1', '1', '00540', '59', '1:50.8', '-0.2', '1,600.0'], ['1986/12/07', '198607030611', '11', '6', '7', '1.5', '1', '1', '00540', '58', '2:19.7', '-0.4', '2,700.0'], ['1986/10/26', '198605040810', '16', '1', '2', '10.7', '3', '9', '00540', '58', '1:59.7', '1.4', ' '], ['1986/09/14', '198609040411', '7', '2', '2', '1.7', '1', '2', '00540', '57', '1:59.7', '0.0', '1,200.0'], ['1986/07/20', '198601020610', '9', '3', '3', '1.2', '1', '1', '00540', '58.5', '1:50.3', '-0.5', '1,400.0'], ['1986/06/29', '198601010809', '8', '3', '3', '2.4', '2', '1', '00540', '55', '2:02.3', '-0.8', '2,700.0'], ['1986/05/11', '198608030811', '17', '6', '12', '9.2', '3', '3', '00540', '54', '2:04.5', '0.3', '730.0'], ['1986/03/30', '198609020411', '10', '2', '2', '17.3', '8', '10', '00588', '56', '2:03.9', '2.3', ' '], ['1985/01/13', '198508010511', '16', '4', '7', '5.4', '1', '1', '00540', '55', '1:37.5', ' ', '2,600.0'], ['1984/12/16', '198407030809', '13', '1', '1', '7.2', '3', '1', '00540', '54', '1:50.1', ' ', '1,200.0'], ['1984/12/08', '198409050305', '9', '1', '1', '2.3', '1', '1', '00540', '54', '1:11.8', ' ', '480.0'], ['1984/11/18', '198408050607', '9', '2', '2', '3.6', '1', '2', '00126', '54', '1:11.6', ' ', '190.0'], ['1984/10/27', '198408040710', '11', '6', '7', '13.6', '6', '9', '00126', '52', '1:37.6', ' ', ' '], ['1984/09/23', '198409040602', '7', '2', '2', '1.6', '1', '1', '00126', '53', '1:14.0', ' ', '440.0'], ['1984/09/09', '198409040206', '13', '3', '3', '10.1', '5', '2', '00126', '53', '1:24.9', ' ', '180.0']]
# 'pass'

# horseフォルダ内からhorseIDを使って情報を取得
def getHorseInfoFromPkl(horseID):
    pathlist = Path("../../dst/scrapingResult/horse").glob('**/*.pickle')
    for path in pathlist:
        if path.name == horseID + ".pickle":
            with open(path, 'rb') as f:
                data = pickle.load(f)
                logger.info('{0} is found'.format(horseID))
                return
    logger.warning('HorseID : {0} is not exist'.format(horseID))

if __name__ == "__main__":
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
    
    # 出力
    printIdx = 0

    logger.info(racedb.raceID[printIdx])
    logger.info(racedb.race_name[printIdx])
    logger.info(racedb.race_data1[printIdx])
    logger.info(racedb.race_data2[printIdx])
    logger.info(racedb.horseIDs_race[printIdx])
    logger.info(racedb.goal_time[printIdx])
    logger.info(racedb.goal_dif[printIdx])
    logger.info(racedb.horse_weight[printIdx])
    logger.info(racedb.money[printIdx])

    index = horsedb.getHorseInfo(racedb.horseIDs_race[0][0])
    logger.debug('HorseIDIndex : {0} '.format(index))
    horsedb.printAllMethodIndex(index)

    # レースでのタイムをsecに変換する
    racedb.goalTimeConv2Sec(printIdx)
    logger.info(racedb.goal_time[printIdx])

    # レースタイムを正規化
    racedb.goalTimeNrm(printIdx)
    logger.info(racedb.goal_time[printIdx])

    # レースごとに入力する
    # 1レースのpklロード
    #  - HorseID参照、展開
    # 正規化(ここが一番たいへん)
    #  - 足りないデータをダミーデータで埋める
    #  - 古いデータの影響度係数をかけてみたりするのもここ
