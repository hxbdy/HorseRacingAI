# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By

import pathlib
import sys
import os
import time
import logging
import csv

# debug initialize
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.disable(logging.DEBUG)

pp_dir = pathlib.Path(__file__).parent
src_dir = pp_dir.parent
root_dir = src_dir.parent
dir_lst = [pp_dir, src_dir, root_dir]
for dir_name in dir_lst:
    if str(dir_name) not in sys.path:
        sys.path.append(str(dir_name))

from scraping import ScrapingUmaData as sud
from common.RaceGradeDB import RaceGradeDB
from common.RaceDB import RaceDB

def save_raceID(driver, yearlist, race_grade_list=["check_grade_4"]):
    # raceIDを取得する．G1~OPまで

    # raceGradedbを読み込む．存在しない場合は新たに作る．
    raceGradedb = sud.read_data("raceGradedbOP")
    if raceGradedb == "FileNotFoundError":
        raceGradedb = RaceGradeDB()

    # 定期的なデータセーブのためのループ回数カウンター
    save_counter = 0

    for year in yearlist:
        raceID_list_year = []
        for start_month in [1,4,7,10]:  # レース数が多すぎるので，四半期ごとに取得
            for race_grade in race_grade_list:
                save_counter += 1

                ## レース種別を入力して検索
                # レース詳細検索に移動
                URL_find_race_id = "https://db.netkeiba.com/?pid=race_search_detail"
                sud.go_page(driver, URL_find_race_id)
                
                # 期間の選択
                sud.select_from_dropdown(driver, "start_year", year)
                sud.select_from_dropdown(driver, "end_year", year)
                sud.select_from_dropdown(driver, "start_mon", start_month)
                sud.select_from_dropdown(driver, "end_mon", start_month+2)
                # 競馬場の選択
                for i in range(1,11): # 全競馬場を選択
                    sud.click_checkbox(driver, "check_Jyo_{:02}".format(i))
                # クラスの選択
                sud.click_checkbox(driver, race_grade)
                # 表示件数を100件にする
                sud.select_from_dropdown(driver, "list", "100")
                # 検索ボタンをクリック
                sud.click_button(driver, "//*[@id='db_search_detail_form']/form/div/input[1]")
                time.sleep(1)

                ## 画面遷移後
                # raceIDをレース名のURLから取得
                # 5列目のデータ全部
                race_column_html = driver.find_elements(By.XPATH, "//*[@class='nk_tb_common race_table_01']/tbody/tr/td[5]")
                raceID_list = []
                for i in range(len(race_column_html)):
                    race_url_str = race_column_html[i].find_element(By.TAG_NAME,"a").get_attribute("href")
                    raceID = race_url_str[race_url_str.find("race/")+5 : -1] # 最後の/を除去
                    raceID_list.append(raceID)

                # raceID_listが日付降順なので、昇順にする
                raceID_list = raceID_list[::-1]

                raceID_list_year = [*raceID_list_year, *raceID_list]

            # raceGradedbに保存
            raceGradedb.appendRaceIDList(raceID_list_year, int(year), race_grade[-1])
            # raceGradedbを10回ごとに外部に出力
            if save_counter % 10 == 0:
                sud.save_data(raceGradedb, "raceGradedbOP")
                logger.info("save raceGradedb comp, year: {}, grade: {}, save_counter:{}"\
                    .format(year, race_grade[-1], save_counter))
        
    # raceGradedbを外部に出力
    sud.save_data(raceGradedb, "raceGradedbOP")

def make_data_set(racedb, start_year, end_year):
    # 重賞を除くOP戦3着馬の走破タイム，レースのデータ(距離，馬場状態，ﾀﾞｰﾄ芝，競馬場, グレード)をリストにする
    # 障害競走は除く
    # [raceID, goaltime(秒), dist, cond, track, loc]
    # cond, type, courseはカテゴリデータ
    # おいっす～
    TARGET_RANK=3
    cond_dict = {'良':1, '稍重':2, '重':3, '不良':4, '良ダート':1, '稍重ダート':2, '重ダート':3, '不良ダート':4} #後半は障害競走のみで使用
    track_dict = {'芝':1, 'ダ': 2, '障':3}
    loc_dict = {'札幌':1, '函館':2, '福島':3, '新潟':4, '東京':5, '中山':6, '中京':7, '京都':8, '阪神':9, '小倉':10}
    grade_dict = {'G1':1, 'G2':2, 'G3':3, 'OP':4, 'J.G1':1, 'J.G2':2, 'J.G3':3}

    data_list = []
    data_list.append(["raceID", "goaltime", "dist", "cond", "track", "loc"]) #1行目は列名
    for i in range(len(racedb.raceID)):
        # start_yearとend_yearの間の期間内でなければリストに入れない
        if int(racedb.raceID[i][0:4]) < start_year or int(racedb.raceID[i][0:4]) > end_year:
            continue
        # 重賞レースは含まない
        if grade_dict[racedb.getRaceGrade(i)] != 4:
            continue
        # 障害競走を除く
        if track_dict[racedb.getTrack(i)] == 3:
            continue
        raceID = racedb.raceID[i]
        goaltime = racedb.goalTimeConv2Sec(racedb.goal_time[i][TARGET_RANK-1])
        dist = racedb.getCourseDistance(i)
        cond = cond_dict[racedb.getCourseCondition(i)]
        track = track_dict[racedb.getTrack(i)]
        loc = loc_dict[racedb.getCourseLocation(i)]

        data_race = [raceID, goaltime, dist, cond, track, loc]
        data_list.append(data_race)
    
    return data_list



if __name__ == '__main__':
    """
    section = 'scraping'
    browser = sud.config.get(section, 'browser')
    driver = sud.start_driver(browser)

    # 保存先フォルダの存在確認
    os.makedirs(sud.OUTPUT_PATH, exist_ok=True)
    
    # netkeibaにログイン
    sud.login(driver, sud.config.get(section, 'mail'), sud.config.get(section, 'pass'))
    
    # OPクラスのレースデータを取得し，racedbOP.pickleに保存する
    START_YEAR = 2010
    END_YEAR = 2020
    RACE_CLASS_LIST =["check_grade_4"]
    logger.info('save_raceID')
    save_raceID(driver, range(START_YEAR,END_YEAR+1), RACE_CLASS_LIST)
    logger.info('save_raceID comp')
    raceGradedb = sud.read_data("raceGradedbOP")
    raceID_list = raceGradedb.getRaceIDList()
    logger.info('save_racedata')
    sud.save_racedata(driver, raceID_list, "racedbOP")
    logger.info('save_racedata comp')

    driver.close()
    """
    # データの整形と出力
    racedb = sud.read_data("racedbOP")
    # 重賞を除くOPクラスレースの2010年から2020年までの10年分のデータを使用
    START_YEAR = 2010
    END_YEAR = 2020
    data = make_data_set(racedb, START_YEAR, END_YEAR)
    with open(str(pp_dir) + "\\dataSet.csv", 'w', newline="") as f:
        writer = csv.writer(f)
        writer.writerows(data)

