import re
import os
import time
import logging
import argparse
import datetime
from dateutil.relativedelta import relativedelta
from multiprocessing        import Process, Queue

from selenium.webdriver.common.by import By

import webdriver_functions as wf
from NetkeibaDB_IF import NetkeibaDB_IF
from file_path_mgr import path_ini, private_ini
from debug         import stream_hdl, file_hdl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("output"))

####################################################################################

# netkeiba上の列名とデータベース上の名前をつなぐ辞書
col_name_dict = {"日付":"date", "開催":"venue", "頭数":"horse_num", "枠番":"post_position", \
        "馬番":"horse_number", "オッズ":"odds", "人気":"fav", "着順":"result", "斤量":"burden_weight", \
            "距離":"distance","馬場":"course_condition", "タイム":"time", "着差":"margin", "賞金":"prize", \
                "レース名":"race_id", "騎手":"jockey_id", "通過":"corner_pos", "ペース":"pace", \
                    "上り":"last_3f", "馬名":"horse_id", "馬体重":"horse_weight", "賞金(万円)":"prize"}

####################################################################################

class horse_prof_table:
    def __init__(self) -> None:
        self.horse_id
        self.bod, 
        self.trainer, 
        self.owner, 
        self.owner_info, 
        self.producer, 
        self.area, 
        self.auction_price, 
        self.earned, 
        self.lifetime_record, 
        self.main_winner, 
        self.relative, 
        self.blood_f, 
        self.blood_ff, 
        self.blood_fm, 
        self.blood_m, 
        self.blood_mf, 
        self.blood_mm, 
        self.horse_title, 
        self.check_flg, 
        self.retired_flg

class race_info_table:
    def __init__(self) -> None:
        self.horse_id, 
        self.race_id, 
        self.date, 
        self.venue, 
        self.horse_num, 
        self.post_position, 
        self.horse_number, 
        self.odds, 
        self.fav, 
        self.result, 
        self.jockey_id, 
        self.burden_weight, 
        self.distance, 
        self.course_condition, 
        self.time, 
        self.margin, 
        self.corner_pos, 
        self.pace, 
        self.last_3f, 
        self.prize, 
        self.grade

class race_result_table:
    def __init__(self) -> None:
        self.horse_id, 
        self.race_id, 
        self.race_name, 
        self.grade, 
        self.race_data1, 
        self.race_data2, 
        self.post_position, 
        self.burden_weight, 
        self.time, 
        self.margin, 
        self.horse_weight, 
        self.prize, 
        self.result

class jockey_info_table:
    def __init__(self) -> None:
        self.jockey_id, 
        self.year, 
        self.num

class untracked_race_id_table:
    def __init__(self) -> None:
        self.race_No
        self.id

class multi_scraper:
    def __init__(self, scrape_list, func, tabs) -> None:
        self.scrape_list = scrape_list
        self.queue = Queue()
        self.func = func
        self.tabs = tabs
        self.child_process = []

        # 子プロセスからのデータ受け取りプロセス生成
        self.rcv = Process(target = self._Task)
        self.rcv.start()

    def scrape(self):
        # スクレイプ予定のリストをプロセス数に分割
        jobs = split_list(self.scrape_list, self.tabs)
        for job in jobs:       
            self.child_process.append(Process(target = self.func, args = (self.queue, job)))
        self._start()
        self._join()

        self.queue.put(["stop"], block=True)
        self.rcv.join()

    def scrape_async(self):
        # 子プロセスの完了を待たずに返る
        # 親プロセスの生成速度 > 子プロセス完了速度
        # の場合、スタックオーバーフローを起こすため使用禁止
        
        # スクレイプ予定のリストをプロセス数に分割
        jobs = split_list(self.scrape_list, self.tabs)
        for job in jobs:       
            self.child_process.append(Process(target = self.func, args = (self.queue, job)))
        self._start()

    def _join(self):
        for process in self.child_process:
            process.join()
        
    def _start(self):
        for process in self.child_process:
            process.start()

class race_multi_scraper(multi_scraper):
    def _Task(self):
        rcv_cnt = 0
        nf = NetkeibaDB_IF("ROM")
        while True:
            rcv = self.queue.get()
            print("race_multi_scraper no.{0}".format(rcv_cnt))
            print("race_multi_scraper wait msg = {0}".format(self.queue.qsize()))
            if(rcv[0] == "success"):
                # race_result テーブルへ挿入
                nf.db_insert_race_result(rcv[1], rcv[2])
                # horse_id リストを更に別プロセスでスクレイプする
                horse_id_list = rcv[3]
                print("1 will scrape horse_id_list = ", horse_id_list)
                nf.db_insert_untracked_horse_id(horse_id_list)
                self.queue.put(["start"], block=True)
            elif(rcv[0] == "start"):
                horse_id_list = nf.db_pop_untracked_horse_id()
                print("2 will scrape horse_id_list = ", horse_id_list)
                ms = horse_multi_scraper(horse_id_list, scrape_horse_result, 5)
                ms.scrape()
            elif(rcv[0] == "failed"):
                print("failed scrape race_id_list = ", rcv[1])
                nf.db_insert_untracked_race_id(rcv[1])
            elif(rcv[0] == "stop"):
                break
            rcv_cnt += 1

class horse_multi_scraper(multi_scraper):
    def _Task(self):
        rcv_cnt = 0
        nf = NetkeibaDB_IF("ROM")
        while True:
            rcv = self.queue.get()
            print("horse_multi_scraper no.{0}".format(rcv_cnt))
            if(rcv[0] == "success"):
                # ["success", horse_prof_data, race_info_data])
                # horse_prof テーブルへ挿入
                nf.db_upsert_horse_prof(rcv[1][0], rcv[1][1], rcv[1][2], rcv[1][3], rcv[1][4], rcv[1][5], rcv[1][6])
                # race_info テーブルへ挿入
                nf.db_diff_insert_race_info(rcv[2][0], rcv[2][1], rcv[2][2])
            elif(rcv[0] == "failed"):
                print("failed scrape horse_id_list = ", rcv[1])
                nf.db_insert_untracked_horse_id(rcv[1])
            elif(rcv[0] == "stop"):
                break
            rcv_cnt += 1

####################################################################################

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

def split_list(l, n):
    """
    リストをサブリストに分割する
    :param l: リスト
    :param n: サブリストの数
    :return: 
    """
    import numpy as np
    res = np.array_split(l, n)
    return res

def url2ID(url, search):
    # urlからsearchの1つ下の階層の文字列を返す
    dom = url.split('/')
    if search in dom:
        return dom[dom.index(search) + 1]
    logger.critical("{0} is not found in {1}".format(search, url))

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
        
        # 進捗表示
        if (iter_num+1) % progress_notice_cycle == 0:
            logger.info("scrape_horsedata {0} / {1} finished.".format(iter_num+1, len(horseID_list)))

        yield [prof_contents, blood_list, horseID, horse_title, check, retired, target_col_hp], [perform_contents, target_col_ri, horseID]
    logger.info("scrape_horsedata comp")


def scrape_racedata(driver, raceID_list):
    """horseIDを取得する & race情報を得る。レースに出走した馬のリストを返す。
    driver: webdriver
    raceID_list: 調べるraceIDのリスト
    """

    # 進捗表示の間隔
    progress_notice_cycle = 10

    for iter_num in range(len(raceID_list)):
        raceID = str(raceID_list[iter_num])
        horseID_list_race = []

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
                if cname == "馬名":
                    horse_id_col_idx = i #horse idの列

        # 各順位のデータを取得
        race_contents = []
        for row in range(1, len(race_table)):
            # 文字列として取得
            race_table_row = race_table[row].find_elements(By.TAG_NAME, "td")
            race_contents_row = list(map(lambda x: x.text, race_table_row))
            # COL_NAME_IDに含まれる列のうち，idを取得可能な場合のみ取得して上書き
            # 現在は馬名のみに対応。他を追加する場合はtry文に変更が必要
            for i in col_idx_id:
                try:
                    horse_url_str = race_table_row[i].find_element(By.TAG_NAME,"a").get_attribute("href")
                    race_contents_row[i] = url2ID(horse_url_str, "horse")
                except:
                    pass
            
            # horse id を別のリストでも記録する
            horseID_list_race.append(race_contents_row[horse_id_col_idx])
            # 必要部分だけ取り出して追加
            race_contents.append(list(map(lambda x: race_contents_row[x], col_idx)))

        ## race_resultテーブルへの保存    
        data_list = []
        for row in race_contents:
            data = [*row, raceID, race_name, race_data1, race_data2, grade]
            data_list.append(data)
        target_col = [*target_col,"race_id","race_name","race_data1","race_data2","grade"]

        # 進捗表示
        if (iter_num+1) % progress_notice_cycle == 0:
            logger.info("scrape_racedata {0} / {1} finished.".format(iter_num+1, len(raceID_list)))

        yield horseID_list_race, target_col, data_list

def scrape_raceID(driver, start_YYMM, end_YYMM, race_grade):
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
        raceID_list.reverse()

        # 検索の開始年月を (ptr + 1) 月からに再設定
        head = ptr + relativedelta(months = 1)

        yield raceID_list

def regist_scrape_race_id(driver, start, end, grade):
    # 期間内のrace_idをuntracked_race_idテーブルへ保存
    grade_dict = {"G1": 1, "G2": 2, "G3": 3, "OP": 4}
    grade_list = re.findall("G1|G2|G3|OP", grade)

    nf = NetkeibaDB_IF("ROM")
    for key in grade_list:
        for race_id_list in scrape_raceID(driver, start, end, grade_dict[key]):

            # 実際にスクレイプするレースを絞るフィルタ処理
            checked_race_id_list = nf.db_filter_scrape_race_id(race_id_list)

            logger.debug("saving checked_race_id_list = {0}".format(checked_race_id_list))
            nf.db_insert_untracked_race_id(checked_race_id_list)

####################################################################################################

def scrape_race_result(queue, race_id_list):
    try:
        browser      = private_ini("scraping", "browser")
        mail_address = private_ini("scraping", "mail")
        password     = private_ini("scraping", "pass")

        driver = wf.start_driver(browser)
        login(driver, mail_address, password)
        for horse_id_list, target_col, data_list in scrape_racedata(driver, race_id_list):
            # 1レースごとに返る
            queue.put(["success", target_col, data_list, horse_id_list], block=True)
    except:
        queue.put(["failed", race_id_list], block=True)

def scrape_horse_result(queue, horse_id_list):
    # TODO: 必要？
    # checked_list = nf.db_not_retired_list(horse_id_list)
    checked_list = horse_id_list
    try:
        browser      = private_ini("scraping", "browser")
        mail_address = private_ini("scraping", "mail")
        password     = private_ini("scraping", "pass")

        driver = wf.start_driver(browser)
        login(driver, mail_address, password)
        for horse_prof_data, race_info_data in scrape_horsedata(driver, checked_list):
            queue.put(["success", horse_prof_data, race_info_data], block=True)
    except:
        queue.put(["failed", checked_list], block=True)

####################################################################################################

def setup_scrape_race_result():
    # get scrape list
    nf = NetkeibaDB_IF("ROM")
    race_id_list = nf.db_pop_untracked_race_id()

    ms = race_multi_scraper(race_id_list, scrape_race_result, 2)
    ms.scrape()

####################################################################################

if __name__ == "__main__":
    # netkeiba ログイン情報読み込み
    browser      = private_ini("scraping", "browser")
    mail_address = private_ini("scraping", "mail")
    password     = private_ini("scraping", "pass")

    # tmpファイルパス読み込み
    path_tmp = path_ini("common", "path_tmp")

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
        
        start = "198601"
        end   = "198602"
        grade = "OP"
        regist_scrape_race_id(driver, start, end, grade)

        driver.close()

        setup_scrape_race_result()

    # 定期的なDBアップデート
    # 1ヶ月間隔更新前提
    elif args.db:
        pass
    
    elif args.race_id:
        pass
    
    else:
        logger.error("read usage: netkeiba_scraping.py -h")
        exit(-1)
