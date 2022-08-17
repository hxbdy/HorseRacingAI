# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import configparser
import time
import os
import pickle
import logging
import sys
import pathlib

# debug initialize
# LEVEL : DEBUG < INFO < WARNING < ERROR < CRITICAL
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.disable(logging.DEBUG)

# commonフォルダ内読み込みのため
scraping_dir = pathlib.Path(__file__).parent
src_dir = scraping_dir.parent
root_dir = src_dir.parent
dir_lst = [scraping_dir, src_dir, root_dir]
for dir_name in dir_lst:
    if str(dir_name) not in sys.path:
        sys.path.append(str(dir_name))

from common.HorseDB import HorseDB
from common.RaceDB import RaceDB
from common.RaceGradeDB import RaceGradeDB
from common.JockeyDB import JockeyDB

OUTPUT_PATH = str(root_dir) + "\\dst\\scrapingResult\\"

"""driverの操作"""
def start_driver(browser):
    """
    ブラウザの起動
    使用ブラウザ: Chrome or FireFox
    """
    if(browser == 'Chrome'):
        # Chromeを起動 (エラーメッセージを表示しない)
        logger.info('initialize chrome driver')
        service = Service(executable_path=ChromeDriverManager().install())
        ChromeOptions = webdriver.ChromeOptions()
        ChromeOptions.add_experimental_option("excludeSwitches", ["enable-logging"])
        ChromeOptions.add_argument('-incognito') # シークレットモード
        # ChromeOptions.add_argument('--headless') # ヘッドレスモード
        driver = webdriver.Chrome(service=service, options=ChromeOptions)
        logger.info('initialize chrome driver comp')
    elif(browser == 'FireFox'):
        # Firefoxを起動
        logger.info('initialize firefox driver')
        FirefoxOptions = webdriver.FirefoxOptions()
        driver_path = str(scraping_dir) + "\\geckodriver.exe"
        driver = webdriver.Firefox(executable_path=driver_path)
        logger.info('initialize firefox driver comp')

    return driver

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

"""pickleでデータを読み込み・保存"""
def read_data(read_file_name):
    """
    scrapingResultフォルダ内にpicle化したファイルを読み込む。
    存在しない場合は文字列を返す．
    """
    try:
        with open(OUTPUT_PATH + read_file_name + ".pickle", "rb") as f:
            data = pickle.load(f)
    except FileNotFoundError:
        data = "FileNotFoundError"
    return data

def save_data(save_data, save_file_name):
    """
    scrapingResultフォルダ内にpicle化したファイルを保存する。
    """
    with open(OUTPUT_PATH + save_file_name + ".pickle", 'wb') as f:
        pickle.dump(save_data, f)

def remove_data(file_name):
    """
    scrapingResultフォルダ内のpickleファイルを削除する
    """
    try:
        os.remove(OUTPUT_PATH + file_name + ".pickle")
    except Exception as e:
        raise e

"""主要部"""
def login(driver, mail_address, password):
    """
    netkeibaにログインする
    """
    go_page(driver, "https://regist.netkeiba.com/account/?pid=login")
    driver.find_element(By.NAME, "login_id").send_keys(mail_address)
    driver.find_element(By.NAME, "pswd").send_keys(password)
    driver.find_element(By.XPATH, "//*[@id='contents']/div/form/div/div[1]/input").click()

def save_raceID(driver, yearlist, race_grade_list=["check_grade_1"]):
    """
    検索をかけてraceIDを取得する。
    [入力] driver: webdriver
    [入力] yearlist: 取得する年のリスト(1986-2022)
    [入力] race_grade_list: 取得するグレードのリスト(G1, G2, opなど) 1: G1, 2: G2, 3: G3, 4: OP
    """
    # raceGradedbを読み込む．存在しない場合は新たに作る．
    raceGradedb = read_data("raceGradedb")
    if raceGradedb == "FileNotFoundError":
        raceGradedb = RaceGradeDB()

    # 定期的なデータセーブのためのループ回数カウンター
    save_counter = 0

    for year in yearlist:
        for race_grade in race_grade_list:
            save_counter += 1

            ## レース種別を入力して検索
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
            click_checkbox(driver, race_grade)
            # 表示件数を100件にする
            select_from_dropdown(driver, "list", "100")
            # 検索ボタンをクリック
            click_button(driver, "//*[@id='db_search_detail_form']/form/div/input[1]")
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
            # raceGradedbに保存
            raceGradedb.appendRaceIDList(raceID_list, int(year), race_grade[-1])
            # raceGradedbを10回ごとに外部に出力
            if save_counter % 10 == 0:
                save_data(raceGradedb, "raceGradedb")
                logger.info("save raceGradedb comp, year: {}, grade: {}, save_counter:{}"\
                    .format(year, race_grade[-1], save_counter))
        
    # raceGradedbを外部に出力
    save_data(raceGradedb, "raceGradedb")

def save_racedata(driver, raceID_list):
    """
    horseIDを取得する & race情報を得る。
    [入力] driver: webdriver
    [入力] raceID_list: 調べるraceIDのリスト
    """
    # racedbを読み込む．存在しない場合は新たに作る．
    racedb = read_data("racedb")
    if racedb == "FileNotFoundError":
        racedb = RaceDB()

    # 定期的なデータセーブのためのループ回数カウンター
    save_counter = 0

    for raceID in raceID_list:
        save_counter += 1

        ## レースページにアクセス
        race_url = "https://db.netkeiba.com/race/{}/".format(raceID)
        logger.info('access {}'.format(race_url))
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
        
        # racedbを10回ごとに外部に出力
        if save_counter % 10 == 0:
            save_data(racedb, "racedb")
            logger.info("save racedb comp, save_counter:{}".format(save_counter))

    save_data(racedb, "racedb")

def save_horsedata(driver, horseID_list, start_count=0):
    """
    馬のデータを取得して保存する
    [入力] horseID_list: 調べるhorseIDのリスト
    [入力] start_count: horseID_listの何番目から探索するか
    (前回がエラーで停止した場合，最後にセーブしたときのsave_counterを入力すると速く開始できる)
    """

    # horsedbを読み込む．存在しない場合は新たに作る．
    horsedb = read_data("horsedb")
    if horsedb == "FileNotFoundError":
        horsedb = HorseDB()
    # 開始前のhorsedbは念のため一次保存しておく
    save_data(horsedb, "horsedb_before_search_tmp")
    
    # 既にhorsedb内に存在するhorseIDを記録する集合
    searched_horseID_set = set(horsedb.horseID)

    # 定期的なデータセーブのためのループ回数カウンター
    save_counter = 0 + start_count
    horseID_list = horseID_list[save_counter:]
    
    for horseID in horseID_list:
        save_counter += 1

        if horseID in searched_horseID_set:
            # horsedbを10回ごとに外部に出力
            if save_counter % 10 == 0:
                save_data(horsedb, "horsedb")
                logger.info("save horsedb comp, save_counter:{}".format(save_counter))
            continue

        ## 馬のページにアクセス
        horse_url = "https://db.netkeiba.com/horse/{}/".format(horseID)
        logger.info('access {}'.format(horse_url))
        go_page(driver, horse_url)
        logger.info('access {} comp'.format(horse_url))
        horsedb.appendHorseID(horseID)

        ## 馬名，英名，抹消/現役，牡牝，毛の色
        # 'コントレイル\nContrail\n抹消\u3000牡\u3000青鹿毛'
        horse_title = driver.find_element(By.CLASS_NAME, "horse_title").text
        horsedb.appendCommon(horse_title)

        ## プロフィールテーブルの取得
        logger.info('get profile table')
        # 過去と現在(2003年ごろ以降に誕生の馬)で表示内容が違うため、tryを使用
        try:
            prof_table = driver.find_element(By.XPATH, "//*[@class='db_prof_table no_OwnerUnit']")
        except:
            prof_table = driver.find_element(By.XPATH, "//*[@class='db_prof_table ']")
        row_name_data = prof_table.find_elements(By.TAG_NAME, "th")
        prof_contents_data = prof_table.find_elements(By.TAG_NAME, "td")
        row_name = []
        prof_contents = []
        for row in range(len(row_name_data)):
            row_name.append(row_name_data[row].text)
            # 調教師の場合はurlから調教師IDを取得し、それ以外はテキストで取得
            if row_name[row] == "調教師":
                try:
                    trainer_url_str = prof_contents_data[row].find_element(By.TAG_NAME, "a").get_attribute("href")
                    trainerID = trainer_url_str[trainer_url_str.find("trainer/")+8 : -1] # 最後の/を除去
                    prof_contents.append(trainerID)
                except:
                    prof_contents.append(prof_contents_data[row].text)
            else:
                prof_contents.append(prof_contents_data[row].text)
            # 競走成績テーブルが全て取得できているか確認するため、出走数を取得しておく
            if row_name[row] == "通算成績":
                num_entry_race = int(prof_contents[row][:prof_contents[row].find("戦")])
        horsedb.appendProfContents(prof_contents)

        ## 血統テーブルの取得
        logger.info('get blood table')
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
        logger.info('get result table')
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
                        try:
                            id_url_str = perform_table_row[col].find_element(By.TAG_NAME, "a").get_attribute("href")
                            # ID_COL_NAMEを変更した場合、ここのif文の変更が必要
                            if icn == "レース名":
                                id = id_url_str[id_url_str.find("race/")+5 : -1]
                            elif icn == "騎手":
                                id = id_url_str[id_url_str.find("jockey/result/recent/")+21 : -1]
                            perform_contents_row.append(id)
                        except:
                            perform_contents_row.append(perform_table_row[col].text)
                        break
            perform_contents.append(perform_contents_row)
        horsedb.appendPerformContents(perform_contents)

        ## 競走成績のデータ取得が成功したかどうかを、通算成績の出走数と競走成績の行数で判定
        if num_entry_race == len(perform_table) -1:
            check = 1 # OK
        else:
            check = 0 # データ欠損アリ (prof_tableとperform_tableで一致しない)
        horsedb.appendCheck(check)

        ## searched_horseID_setの更新と保存処理
        searched_horseID_set.add(horseID)
        # horsedbを10回ごとに外部に出力
        if save_counter % 10 == 0:
            save_data(horsedb, "horsedb")
            logger.info("save horsedb comp, save_counter:{}".format(save_counter))

    save_data(horsedb, "horsedb")
    remove_data("horsedb_before_search_tmp")

        ## 以下保留事項
        # 血統を評価する際に、horseIDs_allから辿れない馬(収集期間内にG1,G2,G3に出場経験のない馬)のhorseIDをどこかに保存しておく
        # 血統テーブルから過去の馬に遡ることになるが、その過去の馬のデータが無い場合どうするか
        # そもそも外国から参加してきた馬はどう処理するのか

def get_jockeyID(horsedb):
    # horsedbから騎手idを取得し、idになっていない値を除いたリストを返す。
    row_jockeyid_list = horsedb.enumAllJockeyID()

    # 一文字でも数字が入っている値のみをidとする
    cleaned_jockeyid_list = []
    for jockeyid in row_jockeyid_list:
        if any(chr.isdigit() for chr in jockeyid):
            cleaned_jockeyid_list.append(jockeyid)
    return cleaned_jockeyid_list

def save_jockeydata(driver, jockeyID_list, start_count=0):
    """
    騎手の年度別成績を取得する.
    save_horsedataと構造は同じ
    """
    jockeydb = read_data("jockeydb")
    if jockeydb == "FileNotFoundError":
        jockeydb = JockeyDB()
    save_data(jockeydb, "jockeydb_before_search_tmp")
    
    searched_jockeyID_set = set(jockeydb.jockeyID)

    save_counter = 0 + start_count
    jockeyID_list = jockeyID_list[save_counter:]

    for jockeyID in jockeyID_list:
        save_counter += 1

        if jockeyID in searched_jockeyID_set:
            if save_counter % 10 == 0:
                save_data(jockeydb, "jockeydb")
                logger.info("save jockeydb comp, save_counter:{}".format(save_counter))
            continue

        ## 騎手の年度別成績ページにアクセス
        url = "https://db.netkeiba.com/jockey/result/{}/".format(jockeyID)
        logger.info('access {}'.format(url))
        go_page(driver, url)
        logger.info('access {} comp'.format(url))

        ## 騎手名と生年月日・所属を取得
        jockey_header = driver.find_element(By.XPATH, "//*[@id='db_main_box']/div/div[1]")
        name = jockey_header.find_element(By.TAG_NAME,"h1").text
        common = jockey_header.find_element(By.TAG_NAME,"p").text

        ## 騎手の年度別成績を取得．年ごとのデータを持ってくる．代表馬はidを取得する．
        # 1985年以降のデータのみ取得する
        YEAR_SINCE = 1985
        result_tbl = driver.find_element(By.CLASS_NAME, "nk_tb_common.race_table_01")
        result_rows = result_tbl.find_elements(By.TAG_NAME, "tr")
        result_rows = result_rows[::-1] # 年度が昇順になるように順番を逆にする
        year_result_list = []
        for row in result_rows:
            row_data = row.find_elements(By.TAG_NAME, "td")
            # 年度の判定
            try:
                year = int(row_data[0].text)
            except ValueError:
                break
            else:
                if year < YEAR_SINCE:
                    continue
            # 内容をリストにする．ダート勝利数までint,収得賞金までfloat化する．
            year_result = []
            for i in range(len(row_data)):
                if i<=19:
                    val = row_data[i].text.replace(",","")
                    if i<=15:
                        year_result.append(int(val))
                    else:
                        year_result.append(float(val))
                else:
                    # 代表馬はidを取得する．ムリなら馬の名前をテキストで取得．
                    try:
                        horse_url_str = row_data[i].find_element(By.TAG_NAME,"a").get_attribute("href")
                        horseID = horse_url_str[horse_url_str.find("horse/")+6 : -1] # 最後の/を除去
                    except:
                        horseID = row_data[i].text
                    year_result.append(horseID)
            year_result_list.append(year_result)
        
        ## 騎手データの保存
        jockeydb.appendJockey(jockeyID, name, common, year_result_list)
        searched_jockeyID_set.add(jockeyID)
        
        # jockeydbを10回ごとに外部に出力
        if save_counter % 10 == 0:
            save_data(jockeydb, "jockeydb")
            logger.info("save jockeydb comp, save_counter:{}".format(save_counter))
    
    save_data(jockeydb, "jockeydb")
    remove_data("jockeydb_before_search_tmp")
                

if __name__ == '__main__':
    # load config
    config = configparser.ConfigParser()
    config.read(str(src_dir) + '\\private.ini')
    section = 'scraping'
    
    # ブラウザ起動
    browser = config.get(section, 'browser')
    driver = start_driver(browser)
    
    # 保存先フォルダの存在確認
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
    # netkeibaにログイン
    login(driver, config.get(section, 'mail'), config.get(section, 'pass'))
    """
    # raceIDを取得してくる
    # データを取得する開始年と終了年
    START_YEAR = 1986
    END_YEAR = 2021
    RACE_CLASS_LIST =["check_grade_1", "check_grade_2", "check_grade_3"]
    logger.info('save_raceID')
    save_raceID(driver, list(range(START_YEAR,END_YEAR+1)), RACE_CLASS_LIST)
    logger.info('save_raceID comp')
    
    # horseIDを取得する & race情報を得る
    logger.info('save_racedata')
    raceGradedb = read_data("raceGradedb")
    raceID_list = raceGradedb.getRaceIDList()
    #raceID_list = ["198606050810"] #test用
    save_racedata(driver, raceID_list)
    logger.info('save_racedata comp')

    # 馬データを取得してくる
    logger.info('save_horsedata')
    racedb = read_data("racedb")
    horseID_list = racedb.getHorseIDList()
    #horseID_list = ["1983104089"] #test用
    save_horsedata(driver, horseID_list)
    logger.info('save_horsedata comp')
    # 欠損データを一部修正
    horsedb = read_data("horsedb")
    horsedb.reconfirmCheck()
    save_data(horsedb, "horsedb")
    
    """ # 調整中
    # 騎手idリストを作成し保存
    logger.info('get_jockeid')
    horsedb = read_data("horsedb")
    jockeyID_list = get_jockeyID(horsedb)
    save_data(jockeyID_list, "jockeyID_list")
    logger.info('get_jockeyid comp')

    # 騎手データを取得してくる
    logger.info('save_jockeydata')
    #jockeyID_list = ['00140'] #test用
    save_jockeydata(driver, jockeyID_list)
    logger.info('save_jockeydata comp')
    
    driver.close()
    
