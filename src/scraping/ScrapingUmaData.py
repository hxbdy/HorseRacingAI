# -*- coding: utf-8 -*-

# commonディレクトリ以下を使用したいため
# scrapingディレクトリにcdしてから実行すること

from tkinter import BROWSE
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
import configparser

import time
import os
import pickle
import logging
from sqlalchemy import TEXT
import sys

# commonフォルダ内読み込みのため
sys.path.append(os.path.abspath(".."))
parentDir = os.path.dirname(os.path.abspath(__file__))
if parentDir not in sys.path:
    sys.path.append(parentDir)

from common.HorseDB import HorseDB
from common.RaceDB import RaceDB

from webdriver_manager.chrome import ChromeDriverManager

OUTPUT_PATH = "../../dst/scrapingResult/"

"""driverの操作"""
def go_page(driver, url):
    """
    url先にアクセス
    """
    driver.get(url)
    time.sleep(1)

def select_from_dropdown(driver, select_name, select_value):
    """
    ドロップダウンから値を選択する
    """
    select = Select(driver.find_element(By.NAME, str(select_name)))
    select.select_by_value(str(select_value))

def click_checkbox(driver, checkbox_id):
    """
    チェックボックスをクリックする
    """
    driver.find_element(By.ID, str(checkbox_id)).click()

def click_button(driver, xpath):
    """
    ボタンをクリックする
    """
    driver.find_element(By.XPATH, xpath).click()

"""pickleでデータを保存"""
def save_data(save_data, save_file_name):
    """
    resultフォルダ内にpicle化したファイルを保存する。
    """
    with open(OUTPUT_PATH + save_file_name + ".pickle", 'wb') as f:
        pickle.dump(save_data, f)

"""主要部"""
def login(driver, mail_address, password):
    """
    netkeibaにログインする
    """
    go_page(driver, "https://regist.netkeiba.com/account/?pid=login")
    driver.find_element(By.NAME, "login_id").send_keys(mail_address)
    driver.find_element(By.NAME, "pswd").send_keys(password)
    driver.find_element(By.XPATH, "//*[@id='contents']/div/form/div/div[1]/input").click()


def get_raceID(driver, yearlist, race_class_list=["check_grade_1"]):
    """
    検索をかけてraceIDを取得する。
    [入力] driver: webdriver
    [入力] yearlist: 取得する年のリスト(1986-2022)
    [入力] race_class_list: 取得するクラスのリスト(G1, G2, opなど) 1: G1, 2: G2, 3: G3, 4: OP
    [出力] raceID_list: raceIDのリスト
    """
    raceID_list = []
    for race_class in race_class_list:
        for year in yearlist:
            # レース詳細検索に移動
            URL_find_race_id = "https://db.netkeiba.com/?pid=race_search_detail"
            go_page(driver, URL_find_race_id)
            
            # 期間の選択
            select_from_dropdown(driver, "start_year", year)
            select_from_dropdown(driver, "end_year", year)
            # 競馬場の選択
            for i in range(1,11): # 全競馬場を選択
                click_checkbox(driver, "check_Jyo_{:02}".format(i))
            # クラスの選択
            click_checkbox(driver, race_class)
            # 表示件数を100件にする
            select_from_dropdown(driver, "list", "100")
            # 検索ボタンをクリック
            click_button(driver, "//*[@id='db_search_detail_form']/form/div/input[1]")
            time.sleep(1)

            ## 画面遷移後
            # raceIDをレース名のURLから取得
            # 5列目のデータ全部
            race_column_html = driver.find_elements(By.XPATH, "//*[@class='nk_tb_common race_table_01']/tbody/tr/td[5]")
            raceIDs_year = []
            for i in range(len(race_column_html)):
                race_url_str = race_column_html[i].find_element(By.TAG_NAME,"a").get_attribute("href")
                raceID = race_url_str[race_url_str.find("race/")+5 : -1] # 最後の/を除去
                raceIDs_year.append(raceID)

            # raceIDs_yearが日付降順なので、昇順にする
            raceIDs_year = raceIDs_year[::-1]

            raceID_list += raceIDs_year

    return raceID_list

def get_horseID_save_racedata(driver, raceID_list):
    """
    horseIDを取得する & race情報を得る。
    [入力] driver: webdriver
    [入力] raceID_list: 調べるraceIDのリスト
    [出力] horseID_set: 出現したhorseIDの集合。
    """
    horseID_set = set()

    racedb = RaceDB()

    for raceID in raceID_list:
        ## レースページにアクセス
        race_url = "https://db.netkeiba.com/race/{}/".format(raceID)
        go_page(driver, race_url)

        racedb.appendRaceID(raceID)

        ## horseIDの取得とhorseID_setへの追加
        horse_column_html = driver.find_elements(By.XPATH, "//*[@class='race_table_01 nk_tb_common']/tbody/tr/td[4]")
        horseIDs_race = []
        for i in range(len(horse_column_html)):
            horse_url_str = horse_column_html[i].find_element(By.TAG_NAME,"a").get_attribute("href")
            horseID = horse_url_str[horse_url_str.find("horse/")+6 : -1] # 最後の/を除去
            horseIDs_race.append(horseID)
        horseID_set |= set(horseIDs_race)
        racedb.appendHorseIDsRace(horseIDs_race)


        ## race情報の取得・整形と保存 (払い戻しの情報は含まず)
        # レース名、レースデータ1(天候など)、レースデータ2(日付など)  <未補正 文字列>
        race_name = driver.find_element(By.XPATH,"//*[@id='main']/div/div/div/diary_snap/div/div/dl/dd/h1").text
        racedb.appendRaceName(race_name)

        race_data1 = driver.find_element(By.XPATH,"//*[@id='main']/div/div/div/diary_snap/div/div/dl/dd/p/diary_snap_cut/span").text
        racedb.appendRaceData1(race_data1)

        race_data2 = driver.find_element(By.XPATH,"//*[@id='main']/div/div/div/diary_snap/div/div/p").text
        racedb.appendRaceData2(race_data2)

        # テーブルデータ
        race_table_data = driver.find_element(By.XPATH, "//*[@class='race_table_01 nk_tb_common']/tbody")
        race_table_data_rows = race_table_data.find_elements(By.TAG_NAME, "tr")
        goal_time = []    #タイム
        goal_dif = []     #着差
        horse_weight = [] #馬体重
        money = []        #賞金
        for row in range(1,len(race_table_data_rows)):
            race_table_row = race_table_data_rows[row].find_elements(By.TAG_NAME, "td")
            goal_time.append(race_table_row[7].text)
            goal_dif.append(race_table_row[8].text)
            horse_weight.append(race_table_row[14].text)
            money.append(race_table_row[-1].text)
        racedb.appendGoalTime(goal_time)
        racedb.appendGoalDiff(goal_dif)
        racedb.appendHorseWeight(horse_weight)
        racedb.appendMoney(money)
        
        # scrapingResult/race内にファイル名raceIDで保存
        race_data = [raceID, race_name, race_data1, race_data2, horseIDs_race, goal_time, goal_dif, horse_weight, money]
        save_data(race_data, "race\\{}".format(raceID))
    save_data(racedb, "racedb")
    
    return horseID_set

def save_horsedata(driver, horseID_list):
    """
    馬のデータを取得して保存する
    [入力] horseID_list: 調べるhorseIDのリスト
    """

    horsedb = HorseDB()

    for horseID in horseID_list:
        ## 馬のページにアクセス
        logger.debug('access netkeiba')
        horse_url = "https://db.netkeiba.com/horse/{}/".format(horseID)
        go_page(driver, horse_url)
        logger.debug('access netkeiba comp')
        
        horsedb.appendHorseID(horseID)

        ## プロフィールテーブルの取得
        logger.debug('get profile table')
        prof_table = driver.find_element(By.XPATH, "//*[@class='db_prof_table no_OwnerUnit']")
        # 過去と現在で表示内容が違うため、行ラベルを認識して整形
        row_name_data = prof_table.find_elements(By.TAG_NAME, "th")
        prof_contents_data = prof_table.find_elements(By.TAG_NAME, "td")
        row_name = []
        prof_contents = []
        for row in range(len(row_name_data)):
            row_name.append(row_name_data[row].text)
            # 調教師の場合はurlから調教師IDを取得し、それ以外はテキストで取得
            if row_name[row] == "調教師":
                trainer_url_str = prof_contents_data[row].find_element(By.TAG_NAME, "a").get_attribute("href")
                trainerID = trainer_url_str[trainer_url_str.find("trainer/")+8 : -1] # 最後の/を除去
                prof_contents.append(trainerID)
            else:
                prof_contents.append(prof_contents_data[row].text)
            # 競走成績テーブルが全て取得できているか確認するため、出走数を取得しておく
            if row_name[row] == "通算成績":
                num_entry_race = int(prof_contents[row][:prof_contents[row].find("戦")])
        horsedb.appendProfContents(prof_contents)

        ## 血統テーブルの取得
        logger.debug('get blood table')
        blood_table = driver.find_element(By.XPATH, "//*[@class='blood_table']")
        blood_table = blood_table.find_elements(By.TAG_NAME, "a")
        # 血統のhorseID。順番：[父, 父父, 父母, 母, 母父, 母母]
        blood_list = []
        for i in range(len(blood_table)):
            blood_horse_url_str = blood_table[i].get_attribute("href")
            blood_horseID = blood_horse_url_str[blood_horse_url_str.find("ped/")+4 : -1]
            blood_list.append(blood_horseID)
        horsedb.appendBloodList(blood_list)

        ## 競走成績テーブルの取得
        logger.debug('get result table')
        perform_table = driver.find_element(By.XPATH, "//*[@class='db_h_race_results nk_tb_common']")
        perform_table = perform_table.find_elements(By.TAG_NAME, "tr")
        # 列名の取得と整形
        column_name_data = perform_table[0].find_elements(By.TAG_NAME, "th")
        column_name = []
        for i in range(len(column_name_data)):
            column_name.append(column_name_data[i].text.replace("\n",""))
        # 競走成績は過去と現在で表示内容が違うため、列名を照合してデータを取得する。
        # TEXT_COL_NAMEとID_COL_NAME にある列のデータだけ取得する。
        # TEXT: 表示されている文字列を取得。ID: レースIDと騎手IDを取得(for文内も変更必要)。
        TEXT_COL_NAME = ["日付", "頭数", "枠番", "馬番", "オッズ", "人気", "着順", "斤量", "タイム", "着差", "賞金"]
        ID_COL_NAME = ["レース名", "騎手"]
        perform_contents = []
        for row in range(1, len(perform_table)):
            perform_table_row = perform_table[row].find_elements(By.TAG_NAME, "td")
            perform_contents_row = []
            for col in range(len(column_name)):
                for tcn in TEXT_COL_NAME:
                    if column_name[col] == tcn:
                        perform_contents_row.append(perform_table_row[col].text)
                        break
                for icn in ID_COL_NAME:
                    if column_name[col] == icn:
                        id_url_str = perform_table_row[col].find_element(By.TAG_NAME, "a").get_attribute("href")
                        # ID_COL_NAMEを変更した場合、ここのif文の変更が必要
                        if icn == "レース名":
                            id = id_url_str[id_url_str.find("race/")+5 : -1]
                        elif icn == "騎手":
                            id = id_url_str[id_url_str.find("jockey/result/recent/")+21 : -1]
                        perform_contents_row.append(id)
                        break
            perform_contents.append(perform_contents_row)
        horsedb.appendPerformContents(perform_contents)

        ## 競走成績のデータ取得が成功したかどうかを、通算成績の出走数と競走成績の行数で判定
        if num_entry_race == len(perform_table) -1:
            check = "pass"
        else:
            check = "lack_data"
        horsedb.appendCheck(check)

        ## 保存処理
        horse_data = [horseID, prof_contents, blood_list, perform_contents, check]
        save_data(horse_data, "horse\\{}".format(horseID))
    save_data(horsedb, "horsedb")

        ## 以下保留事項
        # 血統を評価する際に、horseIDs_allから辿れない馬(収集期間内にG1,G2,G3に出場経験のない馬)のhorseIDをどこかに保存しておく
        # 血統テーブルから過去の馬に遡ることになるが、その過去の馬のデータが無い場合どうするか
        # そもそも外国から参加してきた馬はどう処理するのか

if __name__ == "__main__":

    # debug initialize
    # LEVEL : DEBUG < INFO < WARNING < ERROR < CRITICAL
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s [%(levelname)s] %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    #logger.disable(logging.DEBUG)

    # load config
    config = configparser.ConfigParser()
    config.read('../private.ini')
    section = 'scraping'

    # ブラウザ起動
    # 使用ブラウザ Chrome or FireFox
    if(config.get(section, 'browser') == 'Chrome'):
        # Chromeを起動 (エラーメッセージを表示しない)
        logger.debug('initialize chrome driver')
        service = Service(executable_path=ChromeDriverManager().install())
        ChromeOptions = webdriver.ChromeOptions()
        ChromeOptions.add_experimental_option("excludeSwitches", ["enable-logging"])
        ChromeOptions.add_argument('-incognito') # シークレットモード
        # ChromeOptions.add_argument('--headless') # ヘッドレスモード
        driver = webdriver.Chrome(service=service, options=ChromeOptions)
        logger.debug('initialize chrome driver comp')
    elif(config.get(section, 'browser') == 'FireFox'):
        # Firefoxを起動
        logger.debug('initialize firefox driver')
        FirefoxOptions = webdriver.FirefoxOptions()
        driver = webdriver.Firefox()
        logger.debug('initialize firefox driver comp')
    
    # 保存先フォルダの存在確認
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    os.makedirs(OUTPUT_PATH + "race", exist_ok=True)
    os.makedirs(OUTPUT_PATH + "horse", exist_ok=True)

    # netkeibaにログイン
    login(driver, config.get(section, 'mail'), config.get(section, 'pass'))

    # raceIDを取得してくる
    logger.debug('get_raceID')
    race_class_list =["check_grade_1", "check_grade_2", "check_grade_3"]
    raceID_list = get_raceID(driver, list(range(1986,1987)), race_class_list)
    save_data(raceID_list, "raceID")
    logger.debug('get_raceID comp')
    
    # horseIDを取得する & race情報を得る
    #raceIDs_all = ["198606050810"] #test用
    horseID_set = get_horseID_save_racedata(driver, raceID_list)
    save_data(list(horseID_set), "horseID")

    # 馬データを取得してくる
    #horseID_list = ["1983104089"] #test用
    logger.debug('get_horseID_racedata')
    horseID_list = list(horseID_set)
    save_horsedata(driver, horseID_list)
    logger.debug('get_horseID_racedata comp')

    driver.close()
