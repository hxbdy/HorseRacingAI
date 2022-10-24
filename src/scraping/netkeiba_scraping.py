# -*- coding: utf-8 -*-
import time
import configparser

from selenium.webdriver.common.by import By

from debug import config, logger
import webdriver_functions as wf
from NetkeibaDB import NetkeibaDB

# 現在はスクレイピング側と学習側で使用するDBを使い分けている
# TODO:パスは今後一本化される予定
path_netkeibaDB = config.get('common', 'path_netkeibaDB')
netkeibaDB = NetkeibaDB(path_netkeibaDB)

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


import sqlite3
def create_table():
    """
    現状からの変更メモ
    race_idテーブルを実装．race_idを保持しておく用．レース結果をスクレイプしたかのフラグ管理も一応入れてある．
    horse_profテーブル：horse_title列(馬の名前や英名など)，owner_info列(馬主の募集情報なのでなくてもOK)を追加
    race_infoテーブル：corner_pos列(通過順位)，pace列(レース全体前半3ハロン-レース全体上がり3ハロン)，last_3f列(上がり3ハロン)を追加
    ※paceについて https://oshiete.goo.ne.jp/qa/3358577.html
    race_resultテーブル：result列追加．レース順位を記録．
    """

    """更新用メモ
    netkeibaDB.cur.execute("CREATE TABLE race_id(race_No INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT)")
    netkeibaDB.cur.execute("ALTER TABLE horse_prof ADD COLUMN owner_info")
    netkeibaDB.cur.execute("ALTER TABLE horse_prof ADD COLUMN horse_title")
    netkeibaDB.cur.execute("ALTER TABLE race_info ADD COLUMN corner_pos")
    netkeibaDB.cur.execute("ALTER TABLE race_info ADD COLUMN pace")
    netkeibaDB.cur.execute("ALTER TABLE race_info ADD COLUMN last_3f")
    netkeibaDB.cur.execute("ALTER TABLE race_result ADD COLUMN result")
    netkeibaDB.conn.commit()
    # さらに追加2022/10/25
    netkeibaDB.cur.execute("ALTER TABLE race_result ADD COLUMN post_position")
    """
    dbname = config.get("common", "path_netkeibaDB")
    conn = sqlite3.connect(dbname)
    cur = conn.cursor()
    cur.execute('CREATE TABLE race_id(race_No INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT)')
    cur.execute('CREATE TABLE horse_prof(horse_id PRIMARY KEY, bod, trainer, owner, owner_info, producer, area, auction_price, earned, lifetime_record, main_winner, relative, blood_f, blood_ff, blood_fm, blood_m, blood_mf, blood_mm, horse_title, check_flg)')
    cur.execute('CREATE TABLE race_info(horse_id, race_id, date, venue, horse_num, post_position, horse_number, odds, fav, result, jockey_id, burden_weight, distance, course_condition, time, margin, corner_pos, pace, last_3f, prize, grade, PRIMARY KEY(horse_id, race_id))')
    cur.execute('CREATE TABLE race_result(horse_id, race_id, race_name, race_data1, race_data2, post_position, time, margin, horse_weight, prize, result, PRIMARY KEY(horse_id, race_id))')
    conn.commit()

    cur.close()
    conn.close()


def scrape_raceID(driver, year_month, race_grade="4"):
    """指定期間内のraceIDを取得する。
    driver: webdriver
    year_month: 取得する年月(1986年以降)の指定 <例> ["198601", "202012"] (1986年1月から2020年12月)
    race_grade: 取得するグレードのリスト 1: G1, 2: G2, 3: G3, 4: OP以上全て
    """
    if len(str(year_month[0])) != 6 or len(str(year_month[1])) != 6:
        logger.critical('invalid year_month')
        raise ValueError('年月指定の値が不適切．6桁で指定する．')
    start_year = int(str(year_month[0][:4]))
    start_mon = int(str(year_month[0][4:]))
    end_year = int(str(year_month[1][:4]))
    end_mon = int(str(year_month[1][4:]))
    # 指定年
    year_list = list(range(start_year, end_year+1))
    # 最終年の指定月
    if start_year == end_year:
        month_list_last = list(range(start_mon, end_mon+1))
    else:
        month_list_last = list(range(1, end_mon+1))

    race_grade_name = "check_grade_{}".format(race_grade)


    for year in year_list:
        # スクレイプする月のリスト
        if year == year_list[-1]:
            month_list = month_list_last
        else:
            month_list = list(range(1,13))
        # 四半期(3ヶ月)ごとに分割してデータを取得する          
        for quarter_idx in range(4):
            if len(month_list) <= 3*quarter_idx:
                break
            elif len(month_list) < 3*quarter_idx+3:
                scraping_month = month_list[3*quarter_idx:]
            else:
                scraping_month = month_list[3*quarter_idx:3*quarter_idx+3]

            ## レース種別を入力して検索
            # レース詳細検索に移動
            URL_find_race_id = "https://db.netkeiba.com/?pid=race_search_detail"
            wf.access_page(driver, URL_find_race_id)
            
            # 期間の選択
            wf.select_from_dropdown(driver, "start_year", year)
            wf.select_from_dropdown(driver, "end_year", year)
            wf.select_from_dropdown(driver, "start_mon", scraping_month[0])
            wf.select_from_dropdown(driver, "end_mon", scraping_month[-1])
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
                raceID = race_url_str[race_url_str.find("race/")+5 : -1] # 最後の/を除去
                raceID_list.append(raceID)

            # raceID_listが日付降順なので、昇順にする
            raceID_list = raceID_list[::-1]
            # dbのrace_idテーブルに保存
            logger.debug("saving race_id {0}.{1}-{2} on database started".format(year,scraping_month[0],scraping_month[-1]))
            netkeibaDB.sql_insert_RowToRaceId(raceID_list)
            logger.info("saving race_id {0}.{1}-{2} on database completed".format(year,scraping_month[0],scraping_month[-1]))


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
                logger.info("{0} / {1} finished.".format(iter_num+1, len(raceID_list)))
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

        # raceテーブルのデータを取得
        race_table = driver.find_element(By.XPATH, "//*[@class='race_table_01 nk_tb_common']")
        race_table = race_table.find_elements(By.TAG_NAME, "tr")
        # 取得する列 (順不同)
        COL_NAME_TEXT = ["枠番","タイム","着差","馬体重","賞金(万円)","着順"]
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
                    id = horse_url_str[horse_url_str.find("horse/")+6 : -1] # 最後の/を除去
                    race_contents_row[i] = id
                except:
                    pass
            # 必要部分だけ取り出して追加
            race_contents.append(list(map(lambda x: race_contents_row[x], col_idx)))

        ## race_resultテーブルへの保存    
        data_list = []
        for row in race_contents:
            data = [*row, raceID, race_name, race_data1, race_data2]
            data_list.append(data)
        target_col = [*target_col,"race_id","race_name","race_data1","race_data2"]
        netkeibaDB.sql_insert_Row("race_result", target_col, data_list)
        logger.debug("saving race_result completed, raceID={}".format(raceID))

        # 進捗表示
        if (iter_num+1) % progress_notice_cycle == 0:
            logger.info("{0} / {1} finished.".format(iter_num+1, len(raceID_list)))
    
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
        ## 馬のページにアクセス
        horse_url = "https://db.netkeiba.com/horse/{}/".format(horseID)
        logger.debug('access {}'.format(horse_url))
        wf.access_page(driver, horse_url)

        ## 馬名，英名，抹消/現役，牡牝，毛の色
        # 'コントレイル\nContrail\n抹消\u3000牡\u3000青鹿毛'
        horse_title = driver.find_element(By.CLASS_NAME, "horse_title").text

        ## プロフィールテーブルの取得
        logger.debug('get profile table')
        # 過去と現在(2003年ごろ以降に誕生の馬)で表示内容が違うため、tryを使用
        try:
            prof_table = driver.find_element(By.XPATH, "//*[@class='db_prof_table no_OwnerUnit']")
            target_col_hp = ["horse_id","bod","trainer","owner","producer","area","auction_price","earned","lifetime_record","main_winner","relative","blood_f","blood_ff","blood_fm","blood_m","blood_mf","blood_mm","horse_title","check_flg"]
        except:
            prof_table = driver.find_element(By.XPATH, "//*[@class='db_prof_table ']")
            target_col_hp = ["horse_id","bod","trainer","owner","owner_info","producer","area","auction_price","earned","lifetime_record","main_winner","relative","blood_f","blood_ff","blood_fm","blood_m","blood_mf","blood_mm","horse_title","check_flg"]
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
        race_name_col_idx = 0 # レース名の列位置を保持
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
                race_name_col_idx = i
        target_col_ri.append("grade")
        # 各レースの情報を取得
        perform_contents = []
        for row in range(1, len(perform_table)):
            # 文字列として取得
            perform_table_row = perform_table[row].find_elements(By.TAG_NAME, "td")
            perform_contents_row = list(map(lambda x: x.text, perform_table_row))
            # グレードの判定
            grade = string2grade(perform_contents_row[race_name_col_idx])
            # COL_NAME_IDに含まれる列のうち，idを取得可能な場合のみ取得して上書き
            for i in col_idx_id:
                try:
                    url_str_id = perform_table_row[i].find_element(By.TAG_NAME, "a").get_attribute("href")
                    # レース名か騎手か判定して取得 (ID_COL_NAME変更時にidの取得方法を記述)
                    if "jockey/result/recent/" in url_str_id:
                        id = url_str_id[url_str_id.find("jockey/result/recent/")+21 : -1]
                    elif "race/" in url_str_id:
                        id = url_str_id[url_str_id.find("race/")+5 : -1]
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
        data_list = [[horseID, *prof_contents, *blood_list, horse_title, check]]
        # 存在確認して，あればUPDATE，なければINSERT
        if len(netkeibaDB.sql_mul_tbl("horse_prof",["*"],["horse_id"],[horseID])) > 0:
            netkeibaDB.sql_update_Row("horse_prof", target_col_hp, data_list, ["horse_id = '{}'".format(horseID)])
        else:
            netkeibaDB.sql_insert_Row("horse_prof", target_col_hp, data_list)
        logger.debug("save horsedata on horse_prof table horse_id={}".format(horseID))
        
        #- race_infoテーブル
        # 既にdbに登録されている出走データ数と，スクレイプした出走データ数を比較して，差分を追加
        dif = len(perform_contents) - len(netkeibaDB.sql_mul_tbl("race_info",["*"],["horse_id"],[horseID]))
        logger.debug("dif = {}".format(dif))
        if dif > 0:
            data_list = perform_contents[:dif]
            netkeibaDB.sql_insert_Row("race_info", target_col_ri, data_list)
        else:
            pass
        
        logger.debug("save horsedata completed, horse_id={}".format(horseID))
        # 進捗表示
        if (iter_num+1) % progress_notice_cycle == 0:
            logger.info("{0} / {1} finished.".format(iter_num+1, len(horseID_list)))
    
    logger.info("save_horsedata comp")


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
    """race_resultテーブル内に存在しないraceIDリストを作成
    OP以上のレースに限定するため，race_idテーブルを基にする．
    race_idテーブル -> race_resultテーブル
    """
    #raceID_list_ri = netkeibaDB.cur.execute("SELECT race_id FROM race_id WHERE horse_id > '2019100000'").fetchall()
    raceID_list_ri = netkeibaDB.sql_mul_tbl("race_id",["race_id"],["1"],["1"])
    #raceID_list_ri = list(map(lambda x: x[0], raceID_list_ri))
    raceID_set_ri = set(raceID_list_ri)

    #raceID_list_rr = netkeibaDB.cur.execute("SELECT race_id FROM race_result").fetchall()
    raceID_list_rr = netkeibaDB.sql_mul_tbl("race_result",["DISTINCT race_id"],["1"],["1"])
    #raceID_list_rr = list(map(lambda x: x[0], raceID_list_rr))
    raceID_set_rr = set(raceID_list_rr)

    raceID_list = list(raceID_set_ri - raceID_set_rr)
    # raceIDにアルファベットが入るレースを排除
    raceID_list_out = []
    for raceID in raceID_list:
        if raceID.isdecimal():
            raceID_list_out.append(raceID)

    logger.info(raceID_list_out)
    return raceID_list_out

def write_grade(raceID_list):
    for raceID in raceID_list:
        grade = string2grade(raceID)
        netkeibaDB.sql_update_Row("race_info",["grade"],[[grade]],["race_id = '{}'".format(raceID)])

def string2grade(val):
    """文字列からレースのグレードを判定
    val: 入力文字列
    
    G1, G2, G3, 無印(OP) を判定
    障害競走は J.G1, J.G2, J.G3で返す
    """
    
    #name = netkeibaDB.cur.execute("SELECT race_name FROM race_result WHERE race_id = '{}'".format(raceID))
    #val = val.fetchone()[0]
    if "(G3)" in val:
        return "3"
    elif "(G2)" in val:
        return "2"
    elif "(G1)" in val:
        return "1"
    elif "(J.G3)" in val:
        return "7"
    elif "(J.G2)" in val:
        return "6"
    elif "(J.G1)" in val:
        return "5"
    else:
        return "0"


if __name__ == "__main__":
    config_scraping = configparser.ConfigParser()
    config_scraping.read("src\\private.ini")
    browser = config_scraping.get("scraping", "browser")
    mail_address = config_scraping.get("scraping", "mail")
    password = config_scraping.get("scraping", "pass")
    
    # 後々別のところで管理．
    #create_table()

    """"""
    driver = wf.start_driver(browser)
    login(driver, mail_address, password)
    #scrape_raceID(driver, ["202105", "202108"], 4)
    #scrape_racedata(driver, ["202109021210"])
    scrape_horsedata(driver, ["2018105074"])

    #scrape_horsedata(driver,["2019104476","2019102531","2019100109","2019104909","2019100603","2019101348","2019104937","2019100790","2019105654","2019102632","2019105556","2019100126","2019101507","2019104706","2019104762","2019105366","2019105346","2019105168"])
    
    #raceID_list = make_raceID_list()
    #scrape_racedata(driver, raceID_list)
    #write_grade(raceID_list)

    #driver.close()
