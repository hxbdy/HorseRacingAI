# -*- coding: utf-8 -*-
import time
import configparser
import datetime
import logging
import re
import argparse
import pickle
from dateutil.relativedelta import relativedelta

from selenium.webdriver.common.by import By

import webdriver_functions as wf
from NetkeibaDB import NetkeibaDB
from RaceInfo import RaceInfo
from debug import stream_hdl, file_hdl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("output"))

# load DB
config = configparser.ConfigParser()
config.read('./src/path.ini', 'UTF-8')
path_netkeibaDB = config.get('common', 'path_netkeibaDB')
netkeibaDB = NetkeibaDB(path_netkeibaDB, "ROM")

# netkeiba上の列名とデータベース上の名前をつなぐ辞書
col_name_dict = {"日付":"date", "開催":"venue", "頭数":"horse_num", "枠番":"post_position", \
        "馬番":"horse_number", "オッズ":"odds", "人気":"fav", "着順":"result", "斤量":"burden_weight", \
            "距離":"distance","馬場":"course_condition", "タイム":"time", "着差":"margin", "賞金":"prize", \
                "レース名":"race_id", "騎手":"jockey_id", "通過":"corner_pos", "ペース":"pace", \
                    "上り":"last_3f", "馬名":"horse_id", "馬体重":"horse_weight", "賞金(万円)":"prize"}

def login(driver, mail_address, password):
    """netkeibaにログインする
    """
    wf.access_page(driver, "https://regist.netkeiba.com/account/?pid=login")
    driver.find_element(By.NAME, "login_id").send_keys(mail_address)
    driver.find_element(By.NAME, "pswd").send_keys(password)
    driver.find_element(By.XPATH, "//*[@id='contents']/div/form/div/div[1]/input").click()
    
    # ログインに成功したかの判定
    # もしログインidとパスワードが正しいにも関わらずエラーの場合はこの節を消去する．
    if driver.current_url == "https://regist.netkeiba.com/account/":
        logger.critical('failed to log in netkeiba')
        err_msg = 'ログインに失敗した可能性．ログインidとパスワードを確認してください．正しい場合は，netkeiba_scraping.pyのコードを変更してください．'
        raise ValueError(err_msg)


def create_table():
    import sqlite3
    """データベースの作成
    データベースを新規作成するときに実行する。
    race_idテーブル: race_idを一時的に保持しておく用
    horse_profテーブル: 馬のページにある馬名などの情報と、生年月日などの表・血統の表の情報
    race_infoテーブル: 馬のページにある出走レース情報
    race_resultテーブル: レースのページにあるレース名やレース結果の情報(オッズは含まず)
    jockey_infoテーブル: 騎手の騎乗回数を1年ごとに計上してまとめたテーブル
    """

    dbname = config.get("common", "path_netkeibaDB")
    conn = sqlite3.connect(dbname)
    cur = conn.cursor()
    cur.execute('CREATE TABLE race_id(race_No INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT)')
    cur.execute('CREATE TABLE horse_prof(horse_id PRIMARY KEY, bod, trainer, owner, owner_info, producer, area, auction_price, earned, lifetime_record, main_winner, relative, blood_f, blood_ff, blood_fm, blood_m, blood_mf, blood_mm, horse_title, check_flg, retired_flg)')
    cur.execute('CREATE TABLE race_info(horse_id, race_id, date, venue, horse_num, post_position, horse_number, odds, fav, result, jockey_id, burden_weight, distance, course_condition, time, margin, corner_pos, pace, last_3f, prize, grade, PRIMARY KEY(horse_id, race_id))')
    cur.execute('CREATE TABLE race_result(horse_id, race_id, race_name, grade, race_data1, race_data2, post_position, burden_weight, time, margin, horse_weight, prize, result, PRIMARY KEY(horse_id, race_id))')
    cur.execute('CREATE TABLE jockey_info(jockey_id, year, num, PRIMARY KEY(jockey_id, year))')
    conn.commit()

    cur.close()
    conn.close()


def scrape_raceID(driver, start_YYMM, end_YYMM, race_grade="4"):
    """start_YYMM から end_YYMM までの芝・ダートレースのraceIDを取得する
    driver: webdriver
    start_YYMM: 取得開始年月(1986年以降推奨) <例> "198601" (1986年1月)
    end_YYMM: 取得終了年月(1986年以降推奨) <例> "198601" (1986年1月)
    race_grade: 取得するグレードのリスト 1: G1, 2: G2, 3: G3, 4: OP以上全て
    """

    race_grade_name = "check_grade_{}".format(race_grade)

    try:
        head = datetime.datetime.strptime(start_YYMM, '%Y%m')
        tail = datetime.datetime.strptime(end_YYMM, '%Y%m')
    except:
        logger.critical('invalid year_month[0] = {0}, year_month[1] = {1}'.format(start_YYMM, end_YYMM))
        raise ValueError('年月指定の値が不適切. 6桁で指定する.')
    
    # 期間内のレースIDを取得する
    while head <= tail:
        # head 月から (head+2) 月までのレースを検索
        # 指定範囲を一度にスクレイピングしないのは
        # 通信失敗時のロールバックを抑えるためと検索結果を1ページ(100件)以内に抑えるため
        ptr = head + relativedelta(months = 2)
        if ptr > tail:
            ptr = tail

        ## レース種別を入力して検索
        # レース詳細検索に移動
        URL_find_race_id = "https://db.netkeiba.com/?pid=race_search_detail"
        wf.access_page(driver, URL_find_race_id)
        
        # 芝・ダートのみを選択(障害競走を除外)
        wf.click_checkbox(driver,"check_track_1")
        wf.click_checkbox(driver,"check_track_2")
        # 期間の選択
        wf.select_from_dropdown(driver, "start_year", head.year)
        wf.select_from_dropdown(driver, "end_year", ptr.year)
        wf.select_from_dropdown(driver, "start_mon", head.month)
        wf.select_from_dropdown(driver, "end_mon", ptr.month)
        # 競馬場の選択
        for i in range(1,11): # 全競馬場を選択
            wf.click_checkbox(driver, "check_Jyo_{:02}".format(i))
        # クラスの選択
        wf.click_checkbox(driver, race_grade_name)
        # 表示件数を100件にする
        wf.select_from_dropdown(driver, "list", "100")
        # 検索ボタンをクリック
        wf.click_button(driver, "//*[@id='db_search_detail_form']/form/div/input[1]")
        time.sleep(1)
        ## 画面遷移後
        # raceIDをレース名のURLから取得
        # 5列目のデータ全部
        race_column_html = driver.find_elements(By.XPATH, "//*[@class='nk_tb_common race_table_01']/tbody/tr/td[5]")
        raceID_list = []
        for i in range(len(race_column_html)):
            race_url_str = race_column_html[i].find_element(By.TAG_NAME,"a").get_attribute("href")
            raceID_list.append(url2ID(race_url_str, "race"))
        # raceID_listが日付降順なので、昇順にする
        raceID_list = raceID_list[::-1]
        # dbのrace_idテーブルに保存
        logger.debug("saving race_id {0}.{1}-{2}.{3} on database started".format(head.year, head.month, ptr.year, ptr.month))
        netkeibaDB.sql_insert_RowToRaceId(raceID_list)
        logger.info("saving race_id {0}.{1}-{2}.{3} on database completed".format(head.year, head.month, ptr.year, ptr.month))

        # 検索の開始年月を (ptr + 1) 月からに再設定
        head = ptr + relativedelta(months = 1)


def scrape_racedata(driver, raceID_list):
    """horseIDを取得する & race情報を得る。
    driver: webdriver
    raceID_list: 調べるraceIDのリスト
    """
    # 進捗表示の間隔
    progress_notice_cycle = 10

    for iter_num in range(len(raceID_list)):
        raceID = str(raceID_list[iter_num])

        ## race_resultテーブル内に既に存在しているか判定
        if netkeibaDB.sql_isIn("race_result",["race_id='{}'".format(raceID)]):
            logger.debug("race (raceID={}) is skipped.".format(raceID))
            # 進捗表示
            if (iter_num+1) % progress_notice_cycle == 0:
                logger.info("scrape_racedata {0} / {1} finished.".format(iter_num+1, len(raceID_list)))
            continue

        ## レースページにアクセス
        race_url = "https://db.netkeiba.com/race/{}/".format(raceID)
        logger.debug('access {}'.format(race_url))
        wf.access_page(driver, race_url)


        ## race情報の取得・整形と保存 (払い戻しの情報は含まず)
        # レース名、レースデータ1(天候など)、レースデータ2(日付など)  <未補正 文字列>
        race_name = driver.find_element(By.XPATH,"//*[@id='main']/div/div/div/diary_snap/div/div/dl/dd/h1").text
        race_data1 = driver.find_element(By.XPATH,"//*[@id='main']/div/div/div/diary_snap/div/div/dl/dd/p/diary_snap_cut/span").text
        race_data2 = driver.find_element(By.XPATH,"//*[@id='main']/div/div/div/diary_snap/div/div/p").text

        # グレード判定
        grade_str = race_data1.split("/")[0]
        grade = string2grade(race_name, grade_str)

        # raceテーブルのデータを取得
        race_table = driver.find_element(By.XPATH, "//*[@class='race_table_01 nk_tb_common']")
        race_table = race_table.find_elements(By.TAG_NAME, "tr")
        # 取得する列 (順不同)
        COL_NAME_TEXT = ["枠番","タイム","着差","馬体重","賞金(万円)","着順","斤量"]
        COL_NAME_ID = ["馬名"]
        column_name_data = race_table[0].find_elements(By.TAG_NAME, "th")
        col_idx = []
        col_idx_id = []
        target_col = []
        for i in range(len(column_name_data)):
            # 列名
            cname = column_name_data[i].text.replace("\n","")
            if cname in COL_NAME_TEXT:
                col_idx.append(i)
                target_col.append(col_name_dict[cname])
            elif cname in COL_NAME_ID:
                col_idx_id.append(i)
                col_idx.append(i)
                target_col.append(col_name_dict[cname])
        # 各順位のデータを取得
        race_contents = []
        for row in range(1, len(race_table)):
            # 文字列として取得
            race_table_row = race_table[row].find_elements(By.TAG_NAME, "td")
            race_contents_row = list(map(lambda x: x.text, race_table_row))
            # COL_NAME_IDに含まれる列のうち，idを取得可能な場合のみ取得して上書き
            for i in col_idx_id:
                try:
                    horse_url_str = race_table_row[i].find_element(By.TAG_NAME,"a").get_attribute("href")
                    race_contents_row[i] = url2ID(horse_url_str, "horse")
                except:
                    pass
            # 必要部分だけ取り出して追加
            race_contents.append(list(map(lambda x: race_contents_row[x], col_idx)))

        ## race_resultテーブルへの保存    
        data_list = []
        for row in race_contents:
            data = [*row, raceID, race_name, race_data1, race_data2, grade]
            data_list.append(data)
        target_col = [*target_col,"race_id","race_name","race_data1","race_data2","grade"]
        netkeibaDB.sql_insert_Row("race_result", target_col, data_list)
        logger.debug("save race data on race_result table, raceID={}".format(raceID))

        # 進捗表示
        if (iter_num+1) % progress_notice_cycle == 0:
            logger.info("scrape_racedata {0} / {1} finished.".format(iter_num+1, len(raceID_list)))
    
    logger.info("scrape_racedata comp")


def scrape_horsedata(driver, horseID_list):
    """馬のデータを取得して保存する
    driver: webdriver
    horseID_list: 調べるhorseIDのリスト
    """
    ## 以下保留事項
    # 外国から参加してきた馬はどう処理するのか

    # 進捗表示の間隔
    progress_notice_cycle = 10

    for iter_num in range(len(horseID_list)):
        horseID = str(horseID_list[iter_num])

        ## 引退馬としてテーブルに登録されている場合は飛ばす
        # 注意) JRAへの登録から判定しているため、外国の馬は現状飛ばせない。例: モンジュー
        if netkeibaDB.sql_isIn("horse_prof",["horse_id='{}'".format(horseID),"retired_flg='1'"]):
            logger.debug("horse (horseID={}) is skipped.".format(horseID))
            # 進捗表示
            if (iter_num+1) % progress_notice_cycle == 0:
                logger.info("scrape_horsedata {0} / {1} finished.".format(iter_num+1, len(horseID_list)))
            continue

        ## 馬のページにアクセス
        horse_url = "https://db.netkeiba.com/horse/{}/".format(horseID)
        logger.debug('access {}'.format(horse_url))
        wf.access_page(driver, horse_url)

        ## 馬名，英名，抹消/現役，牡牝，毛の色
        # 'コントレイル\nContrail\n抹消\u3000牡\u3000青鹿毛'
        horse_title = driver.find_element(By.CLASS_NAME, "horse_title").text
        # 引退馬判定 (現役:0, 引退:1)
        if "抹消" in horse_title:
            retired = "1"
        else:
            retired = "0"

        ## プロフィールテーブルの取得
        logger.debug('get profile table')
        # 過去と現在(2003年ごろ以降に誕生の馬)で表示内容が違うため、tryを使用
        try:
            prof_table = driver.find_element(By.XPATH, "//*[@class='db_prof_table no_OwnerUnit']")
            target_col_hp = ["bod","trainer","owner","producer","area","auction_price","earned","lifetime_record","main_winner","relative"]
        except:
            prof_table = driver.find_element(By.XPATH, "//*[@class='db_prof_table ']")
            target_col_hp = ["bod","trainer","owner","owner_info","producer","area","auction_price","earned","lifetime_record","main_winner","relative"]
        target_col_hp = [*target_col_hp, "blood_f","blood_ff","blood_fm","blood_m","blood_mf","blood_mm", "horse_id","horse_title","check_flg","retired_flg"] #★順序対応確認
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
                    prof_contents.append(url2ID(trainer_url_str, "trainer"))
                except:
                    prof_contents.append(prof_contents_data[row].text)
            else:
                prof_contents.append(prof_contents_data[row].text)
            # 競走成績テーブルが全て取得できているか確認するため、出走数を取得しておく
            if row_name[row] == "通算成績":
                num_entry_race = int(prof_contents[row][:prof_contents[row].find("戦")])

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

        ## 競走成績テーブルの取得
        logger.debug('get result table')
        perform_table = driver.find_element(By.XPATH, "//*[@class='db_h_race_results nk_tb_common']")
        perform_table = perform_table.find_elements(By.TAG_NAME, "tr")
        # 取得する列の位置を決定する (過去と現在で表の形が異なるため)
        # COL_NAME_TEXTとCOL_NAME_ID にある列のデータだけ取得する。
        # TEXT: 表示されている文字列を取得。ID: レースIDと騎手IDを取得(下のtry文内も変更必要)。
        COL_NAME_TEXT = ["日付","開催", "頭数", "枠番", "馬番", "オッズ", "人気", "着順", "斤量","距離","馬場", "タイム", "着差", "賞金", "通過", "ペース", "上り"]
        COL_NAME_ID = ["レース名", "騎手"]
        column_name_data = perform_table[0].find_elements(By.TAG_NAME, "th")
        col_idx = []
        col_idx_id = []
        col_idx_for_grade = [-1, -1] # グレード判定用の列の位置を保持(レース名、距離)
        target_col_ri = ["horse_id"]
        for i in range(len(column_name_data)):
            # 列名
            cname = column_name_data[i].text.replace("\n","")
            if cname in COL_NAME_TEXT:
                col_idx.append(i)
                target_col_ri.append(col_name_dict[cname])
            elif cname in COL_NAME_ID:
                col_idx_id.append(i)
                col_idx.append(i)
                target_col_ri.append(col_name_dict[cname])
            if cname == "レース名":
                col_idx_for_grade[0] = i
            elif cname == "距離":
                col_idx_for_grade[1] = i
        target_col_ri.append("grade")
        # 各レースの情報を取得
        perform_contents = []
        for row in range(1, len(perform_table)):
            # 文字列として取得
            perform_table_row = perform_table[row].find_elements(By.TAG_NAME, "td")
            perform_contents_row = list(map(lambda x: x.text, perform_table_row))
            # グレードの判定
            grade = string2grade(perform_contents_row[col_idx_for_grade[0]],perform_contents_row[col_idx_for_grade[1]])
            # COL_NAME_IDに含まれる列のうち，idを取得可能な場合のみ取得して上書き
            for i in col_idx_id:
                try:
                    url_str_id = perform_table_row[i].find_element(By.TAG_NAME, "a").get_attribute("href")
                    # レース名か騎手か判定して取得 (ID_COL_NAME変更時にidの取得方法を記述)
                    if "jockey/result/recent/" in url_str_id:
                        id = url2ID(url_str_id, "recent")
                    elif "race/" in url_str_id:
                        id = url2ID(url_str_id, "race")
                    perform_contents_row[i] = id
                except:
                    pass
            # 必要部分だけ取り出して追加
            perform_contents.append([horseID, *list(map(lambda x: perform_contents_row[x], col_idx)), grade])

        ## 競走成績のデータ取得が成功したかどうかを、通算成績の出走数と競走成績の行数で判定
        if num_entry_race == len(perform_contents):
            check = "1" # OK
        else:
            check = "0" # データ欠損アリ (prof_tableとperform_tableで一致しない)


        ## テーブルへの保存
        #- horse_profテーブル
        data_list = [[*prof_contents, *blood_list, horseID, horse_title, check, retired]] #★順序対応確認
        # 存在確認して，あればUPDATE，なければINSERT
        if len(netkeibaDB.sql_mul_tbl("horse_prof",["*"],["horse_id"],[horseID])) > 0:
            netkeibaDB.sql_update_Row("horse_prof", target_col_hp, data_list, ["horse_id = '{}'".format(horseID)])
        else:
            netkeibaDB.sql_insert_Row("horse_prof", target_col_hp, data_list)
        logger.debug("save horse data on horse_prof table, horse_id={}".format(horseID))
        
        #- race_infoテーブル
        # 既にdbに登録されている出走データ数と，スクレイプした出走データ数を比較して，差分を追加
        dif = len(perform_contents) - len(netkeibaDB.sql_mul_tbl("race_info",["*"],["horse_id"],[horseID]))
        logger.debug("dif = {}".format(dif))
        if dif > 0:
            data_list = perform_contents[:dif]
            netkeibaDB.sql_insert_Row("race_info", target_col_ri, data_list)
        else:
            pass
        logger.debug("save horse data on race_info table, horse_id={}".format(horseID))
        
        # 進捗表示
        if (iter_num+1) % progress_notice_cycle == 0:
            logger.info("scrape_horsedata {0} / {1} finished.".format(iter_num+1, len(horseID_list)))
    logger.info("scrape_horsedata comp")


def scrape_race_today(driver, raceID):
    """まだ競走が始まっていないレースのデータをスクレイプする
    driver: webdriver
    raceID: レースid
    """
    raceInfo = RaceInfo()
    raceInfo.race_id = raceID
    
    # サイトにアクセス
    url = "https://race.netkeiba.com/race/shutuba.html?race_id={}&rf=top_pickup".format(str(raceID))
    wf.access_page(driver, url)

    # 予測に必要なデータをスクレイプ
    race_date_raw = driver.find_element(By.ID, "RaceList_DateList").find_element(By.CLASS_NAME, "Active").text  # '10月30日(日)' or '12/17'
    year = int(raceID[:4])
    month_day = re.findall(r"\d+", race_date_raw)
    raceInfo.date = datetime.date(year, int(month_day[0]), int(month_day[1]))

    # 文中から
    racedata01 = driver.find_element(By.CLASS_NAME, "RaceData01").text # '14:50発走 / ダ1200m (右) / 天候:晴 / 馬場:良'
    logger.debug("racedata01 = {0}".format(racedata01))

    racedata01 = racedata01.split("/")
    raceInfo.start_time = racedata01[0][:racedata01[0].find("発走")]        # '14:50'
    raceInfo.distance = [float(re.findall('\d{3,4}', racedata01[1])[0])]   # [1200.0]

    try:
        # レース前に天候, 馬場が取得できない時は晴、良とする
        raceInfo.weather = racedata01[2][racedata01[2].find(":")+1:].strip(" ") # '晴'
        raceInfo.course_condition = racedata01[3][racedata01[3].find(":")+1:]   # '良'
    except IndexError:
        logger.error("!!! IndexError : racedata01 = {0}".format(racedata01))
        raceInfo.weather = '晴'
        raceInfo.course_condition = '良'
    
    racedata02 = driver.find_element(By.CLASS_NAME, "RaceData02").find_elements(By.TAG_NAME, "span")
    #venue = racedata02[1].text            # '中山'
    prize_str = racedata02[-1].text       # '本賞金:1840,740,460,280,184万円'
    raceInfo.prize = re.findall(r"\d+", prize_str) # ['1840', '740', '460', '280', '184']

    # テーブルから
    shutuba_table = driver.find_element(By.XPATH, "//*[@class='Shutuba_Table RaceTable01 ShutubaTable tablesorter tablesorter-default']")

    COL_NAME_TEXT = ["枠", "馬番", "斤量"]
    COL_NAME_ID = ["馬名", "騎手"]
    column_name_data = shutuba_table.find_elements(By.TAG_NAME, "th")
    col_idx = []
    col_idx_id = []
    target_col = []
    for i in range(len(column_name_data)):
        # 列名
        cname = column_name_data[i].text.replace("\n","")
        if cname in COL_NAME_TEXT:
            col_idx.append(i)
            target_col.append(cname)
        elif cname in COL_NAME_ID:
            col_idx_id.append(i)
            col_idx.append(i)
            target_col.append(cname)
    contents = []
    shutuba_table = shutuba_table.find_element(By.TAG_NAME, "tbody")
    shutuba_table = shutuba_table.find_elements(By.TAG_NAME, "tr")
    for row in range(len(shutuba_table)):
        # 文字列として取得
        shutuba_table_row = shutuba_table[row].find_elements(By.TAG_NAME, "td")
        shutuba_contents_row = list(map(lambda x: x.text, shutuba_table_row))
        # COL_NAME_IDに含まれる列のうち，idを取得可能な場合のみ取得して上書き
        for i in col_idx_id:
            try:
                url_str_id = shutuba_table_row[i].find_element(By.TAG_NAME, "a").get_attribute("href")
                # レース名か騎手か判定して取得 (ID_COL_NAME変更時にidの取得方法を記述)
                if "jockey/result/recent/" in url_str_id:
                    id = url2ID(url_str_id, "recent")
                elif "horse/" in url_str_id:
                    id = url2ID(url_str_id, "horse")
                shutuba_contents_row[i] = id
            except:
                pass
        # 必要部分だけ取り出して追加
        contents.append(list(map(lambda x: shutuba_contents_row[x], col_idx)))
    
    raceInfo.horse_num = len(shutuba_table)
    raceInfo.post_position = list(map(lambda x: int(x[0]), contents))
    raceInfo.horse_number = list(map(lambda x: int(x[1]), contents))
    raceInfo.horse_id = list(map(lambda x: x[2], contents))
    raceInfo.burden_weight = list(map(lambda x: float(x[3]), contents))
    raceInfo.jockey_id = list(map(lambda x: x[4], contents))
    
    print("枠")
    print(raceInfo.post_position)
    print("馬番")
    print(raceInfo.horse_number)
    print("horse id")
    print(raceInfo.horse_id)
    print("斤量")
    print(raceInfo.burden_weight)
    print("jockey id")
    print(raceInfo.jockey_id)
    print("発走時刻")
    print(raceInfo.start_time)
    print("距離")
    print(raceInfo.distance)
    print("天候")
    print(raceInfo.weather)
    print("馬場状態")
    print(raceInfo.course_condition)
    print("本賞金")
    print(raceInfo.prize)
    return raceInfo
    

def reconfirm_check():
    """check_flgが0の馬を再確認して修正可能なら修正する
    db上のデータを削除することはせず，flgの値のみ変更する．
    """
    # checkが0の馬のhorse_idを抽出
    id_check_list = netkeibaDB.sql_mul_tbl("horse_prof",["horse_id"],["check_flg"],["0"])
    logger.info("{} horses need be reconfirmed.".format(len(id_check_list)))
    logger.info("horse_id:")
    logger.info(id_check_list)

    # 修正処理
    idx_list = []
    for horse_id in id_check_list:
        # エラーを含むレース数のカウンター
        num_error = 0
        # 着順による判定
        result_list = netkeibaDB.sql_mul_tbl("race_info",["result"],["horse_id"],horse_id)
        for res in result_list:
            # 着順が "除","取","" のレースを除外 (競走除外，出走取消，開催延期?)
            if res == "除" or res == "取" or res == "":
                num_error += 1
        # horse_profの通算成績の競走回数と比較
        race_prof = netkeibaDB.sql_mul_tbl("horse_prof",["lifetime_record"],["horse_id"],horse_id)[0]
        if int(race_prof) == len(result_list) - num_error:
            netkeibaDB.sql_update_Row("horse_prof",["check_flg"],["1"],["horse_id = '{}'".format(horse_id)])
    
    # checkが0の馬のhorse_idを再抽出して表示
    id_check_list = netkeibaDB.sql_mul_tbl("horse_prof",["horse_id"],["check_flg"],["0"])
    logger.info("{} horses remained.".format(len(id_check_list)))
    logger.info("horse_id:")
    logger.info(id_check_list)

    logger.info("reconfirm_check comp")


def make_raceID_list():
    """race_idテーブルに存在し、かつrace_resultテーブル内に存在しないレースのraceIDリストを返す
    race_idテーブル -> race_resultテーブル
    """
    raceID_list_ri = netkeibaDB.sql_mul_tbl("race_id",["DISTINCT id"],["1"],[1])
    raceID_set_ri = set(raceID_list_ri)
    raceID_list_rr = netkeibaDB.sql_mul_tbl("race_result",["DISTINCT race_id"],["1"],[1])
    raceID_set_rr = set(raceID_list_rr)

    raceID_list = list(raceID_set_ri - raceID_set_rr)
    # raceIDにアルファベットが入るレースを排除
    raceID_list_out = []
    for raceID in raceID_list:
        if raceID.isdecimal():
            raceID_list_out.append(raceID)

    logger.info("race id list ->")
    logger.info(raceID_list_out)
    return raceID_list_out

def make_horseID_list():
    """race_resultテーブル内に存在し、かつ引退していない馬のhorse_idリストを返す
    race_resultテーブル -> horse_profテーブル
    """
    horseID_list_rr = netkeibaDB.sql_mul_tbl("race_result",["DISTINCT horse_id"],["1"],[1])
    horseID_set_rr = set(horseID_list_rr)
    horseID_list_hp = netkeibaDB.sql_mul_tbl("horse_prof",["horse_id"],["retired_flg"],["0"])
    horseID_set_hp = set(horseID_list_hp)

    horseID_list = list(horseID_set_rr - horseID_set_hp)
    # horseIDにアルファベットが入る馬を排除
    horseID_list_out = []
    for horseID in horseID_list:
        if horseID.isdecimal():
            horseID_list_out.append(horseID)
    
    logger.debug("horse id list ->")
    logger.debug(horseID_list_out)
    return horseID_list_out


def write_grade(raceID_list):
    for raceID in raceID_list:
        db_search = netkeibaDB.cur.execute("SELECT race_name, race_data1 FROM race_result WHERE race_id='{}' LIMIT 1".format(raceID)).fetchall()
        if len(db_search) == 0:
            continue
        grade = string2grade(db_search[0], db_search[1].split("/")[0])
        netkeibaDB.sql_update_Row("race_result",["grade"],[[grade]],["race_id = '{}'".format(raceID)])

def string2grade(grade_str, distance_str):
    """文字列からレースのグレードを判定
    grade_str: グレードが入っている文字列
    distance_str: 芝/ダート/障害の情報が入っている文字列
    
    芝 G1: 1, G2: 2, G3: 3, 無印(OP): 4
    ダ G1: 6, G2: 7, G3: 8, 無印(OP): 9
    障 J.G1: 11, J.G2: 12, J.G3: 13, 無印(OP): 14
    """
    grade = 0
    if "障" in distance_str:
        grade += 10
    elif "ダ" in distance_str:
        grade += 5

    if "(G3)" in grade_str:
        grade += 3
    elif "(G2)" in grade_str:
        grade += 2
    elif "(G1)" in grade_str:
        grade += 1
    elif "(J.G3)" in grade_str:
        grade += 3
    elif "(J.G2)" in grade_str:
        grade += 2
    elif "(J.G1)" in grade_str:
        grade += 1
    else:
        grade += 4
    
    return str(grade)

def url2ID(url, search):
    # urlからsearchの1つ下の階層の文字列を返す
    dom = url.split('/')
    if search in dom:
        return dom[dom.index(search) + 1]
    logger.critical("{0} is not found in {1}".format(search, url))

def update_database(driver, start_YYMM, end_YYMM, race_grade="4"):
    """データベース全体を更新する
    driver: webdriver
    start_YYMM: 取得開始年月(1986年以降推奨) <例> "198601" (1986年1月)
    end_YYMM: 取得終了年月(1986年以降推奨) <例> "198601" (1986年1月)
    race_grade: 取得するグレードのリスト 1: G1, 2: G2, 3: G3, 4: OP以上全て
    """
    # 期間内のrace_idを取得してrace_idテーブルへ保存
    scrape_raceID(driver, start_YYMM, end_YYMM, race_grade)

    # 未調査のrace_idのリストを作成
    raceID_list = make_raceID_list()

    # レース結果をスクレイプしてrace_resultテーブルへ保存
    scrape_racedata(driver, raceID_list)

    # 前回調査時点で引退していない馬のみのhorse_idリストを作成
    horseID_list = make_horseID_list()

    # 馬の情報をスクレイプしてhorse_profテーブルとrace_infoテーブルへ保存
    scrape_horsedata(driver, horseID_list)

    # データ整合性チェック
    #reconfirm_check()

    # 騎手の騎乗回数を更新
    head_year = datetime.datetime.strptime(start_YYMM, '%Y%m').year
    tail_year = datetime.datetime.strptime(end_YYMM, '%Y%m').year
    update_jockey_info(head_year, tail_year)


    logger.info("update_database comp")

def update_horsedata_only(driver, horseID_list):
    """レース直前にレースに出走する馬に関係する情報のみ集める
    レースの予想に必要なのはrace_infoテーブル。
    scrape_horsedataを実行し、race_infoとhorse_profを更新する。
    driver: webdriver
    horseID_list: レースに出走する馬のhorse idのリスト
    """
    scrape_horsedata(driver, horseID_list)
    #reconfirm_check()
    logger.info("update_horsedata_only comp")
    
def update_jockey_info(lower_year=1980, upper_year=2021):
    """jockey_infoテーブルの更新
    開始年から終了年までの各年で、騎手の騎乗回数をカウントしてテーブルを更新。
    騎乗回数はrace_infoテーブルから計上する。
    lower_year: 開始年
    upper_year: 終了年
    """
    # 各年30秒ほどかかる

    for year in list(range(lower_year, upper_year+1)):
        year = str(year)
        year0 = year + "00000000"
        year1 = year + "99999999"

        # (year)年に騎乗した騎手のリスト
        jockey_list_raw = netkeibaDB.cur.execute("SELECT DISTINCT jockey_id FROM race_info WHERE race_id>'{0}' AND race_id<'{1}'".format(year0,year1)).fetchall()
        jockey_list = list(map(lambda x: x[0], jockey_list_raw))
        
        logger.info("year {}, #jockey = {}".format(year, len(jockey_list)))
        col_list = ["jockey_id", "year", "num"]
        data_list_update = []
        data_list_insert = []
        for jockey_id in jockey_list:
            # 騎乗回数のカウント
            cnt = netkeibaDB.sql_one_rowCnt_range("race_info", "jockey_id", jockey_id, year0, year1)
            data_list = [jockey_id, year, str(cnt)]
            condition_list = ["jockey_id='{}'".format(data_list[0]), "year='{}'".format(data_list[1])]
            if netkeibaDB.sql_isIn("jockey_info", condition_list):
                data_list_update.append(data_list)
            else:
                data_list_insert.append(data_list)
        
        # dbの更新
        if len(data_list_update) > 0:
            for data_list in data_list_update:
                condition_list = ["jockey_id='{}'".format(data_list[0]), "year='{}'".format(data_list[1])]
                netkeibaDB.sql_update_Row("jockey_info", col_list, [data_list], condition_list)
        if len(data_list_insert) > 0:
            netkeibaDB.sql_insert_Row("jockey_info", col_list, data_list_insert)

        logger.info("year {} end".format(year))
    


if __name__ == "__main__":
    # netkeiba ログイン情報読み込み
    config_scraping = configparser.ConfigParser()
    config_scraping.read("./src/private.ini", 'UTF-8')
    browser      = config_scraping.get("scraping", "browser")
    mail_address = config_scraping.get("scraping", "mail")
    password     = config_scraping.get("scraping", "pass")

    # tmpファイルパス読み込み
    config_tmp = configparser.ConfigParser()
    config_tmp.read("./src/path.ini", 'UTF-8')
    path_tmp = config_tmp.get("common", "path_tmp")

    # 引数パース
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--init', action='store_true', default=False, help='init database and scrape until today')
    parser.add_argument('-d','--db', action='store_true', default=False, help='update database')
    parser.add_argument('-r','--race_id', help='scrape race_id info')
    args = parser.parse_args()

    # DB初期化
    if args.init:
        driver = wf.start_driver(browser)
        login(driver, mail_address, password)
        
        create_table()
        start = "198601"
        end = datetime.datetime.now().strftime("%Y%m")
        update_database(driver, start, end)

    # 定期的なDBアップデート
    # 1ヶ月間隔更新前提
    elif args.db:
        driver = wf.start_driver(browser)
        login(driver, mail_address, password)

        end = datetime.datetime.now()
        start = end - relativedelta(months=1)

        end = end.strftime("%Y%m")
        start = start.strftime("%Y%m")

        logger.info("start = {0}, end = {1}".format(start, end))
        update_database(driver, start, end)
    
    elif args.race_id:
        driver = wf.start_driver(browser)
        login(driver, mail_address, password)

        # 当日予想したいレースIDから馬の情報をコンソール出力
        a = scrape_race_today(driver, args.race_id)

        # 出走する馬のDB情報をアップデート
        update_horsedata_only(driver, a.horse_id)

        # 推測用に取得したレース情報を一時保存
        with open(path_tmp, 'wb') as f:
            pickle.dump(a, f)
    
    else:
        logger.error("read usage: netkeiba_scraping.py -h")
        exit(-1)

    driver.close()
