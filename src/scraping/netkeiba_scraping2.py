import re
import os
import time
import logging
import argparse
import datetime
from dateutil.relativedelta import relativedelta
from multiprocessing        import Process, Queue
from collections            import deque

from selenium.webdriver.common.by import By
import pandas as pd

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
col_name_dict = {"日付":"date", "開催":"venue", "頭数":"horse_num", "枠 番":"post_position", \
        "馬番":"horse_number", "オッズ":"odds", "人気":"fav", "着 順":"result", "斤量":"burden_weight", \
            "距離":"distance","馬場":"course_condition", "タイム":"time", "着差":"margin", "賞金":"prize", \
                "レース名":"race_id", "騎手":"jockey_id", "通過":"corner_pos", "ペース":"pace", \
                    "上り":"last_3f", "馬名":"horse_id", "馬体重":"horse_weight", "賞金 (万円)":"prize"}

####################################################################################

# TODO: 順序付き辞書(初期値None)を用意しておいて、スクレイプ結果をここに詰めていく。
# それぞれのクラスでwebページ上の表記と、DB上の表記を変換する関数を用意する
# set(web上の列名, データ) 
# 列名をDB用列名に変換して、データを変数として持っておく

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

def main_process(queue, untracked_race_id_list, children_num):
    children_process  = []
    children_queue    = []
    children_comp_flg = [0] * children_num
    
    nf = NetkeibaDB_IF("ROM")

    untracked_race_id_queue  = deque(untracked_race_id_list)
    untracked_horse_id_queue = deque()

    # 前回 FAILED した id があればエンキューしておく
    untracked_race_id_queue.extend(nf.db_pop_untracked_race_id())
    untracked_horse_id_queue.extend(nf.db_pop_untracked_horse_id())

    # スクレイププロセスの用意
    # REQ メッセージをエンキュー
    for i in range(children_num):
        children_queue.append(Queue())
        children_process.append(Process(target=scrape_process, args=(queue, children_queue[-1], i)))
        children_process[-1].start()
        queue.put(["REQ", i])

    while True:
        data = queue.get()

        # REQ メッセージ
        # 子プロセスからジョブの要求があったときに受信する
        # 未スクレイプの horse_id / race_id があれば子プロセスにスクレイプ要求を送信する
        if data[0] == "REQ":
            children_id = data[1]

            # スクレイピング待ちの馬のidをデキュー
            # レース1回につき馬は複数いるので、馬のスクレイプ優先
            if len(untracked_horse_id_queue) < (children_num * 2):
                if len(untracked_race_id_queue) != 0:
                    cat  = "REQ"
                    id   = untracked_race_id_queue.pop()
                    func = scrape_race_result
                elif len(untracked_horse_id_queue) != 0:
                    cat  = "REQ"
                    id   = untracked_horse_id_queue.pop()
                    func = scrape_horse_result
                else:
                    # FIN メッセージ
                    # horse_id / race_id のキューが空なら
                    # 子プロセスに終了要求を送信する準備をする
                    cat  = "FIN"
                    id   = None
                    func = None
                    children_comp_flg[children_id] = 1   
            else:
                cat  = "REQ"
                id   = untracked_horse_id_queue.pop()
                func = scrape_horse_result
            
            # 子プロセスに各種要求送信
            children_queue[children_id].put([cat, children_id, func, id])

        # 子プロセスからのスクレイプ完了通知
        elif data[0] == "SUCCESS":
            
            # レースのスクレイプ完了通知受信
            # race_result テーブルの更新と
            # そのレースに出走した horse_id をエンキューする
            if data[1] == "scrape_race_result":
                race_result = data[2]
                #TODO: data frameの挿入処理

            # 馬のスクレイプ完了通知受信
            # horse_prof / race_info テーブルの更新
            elif data[1] == "scrape_horse_result":
                horse_prof_data, race_info_data = data[2]
                nf.db_upsert_horse_prof(horse_prof_data[0], horse_prof_data[1], horse_prof_data[2], horse_prof_data[3], horse_prof_data[4], horse_prof_data[5], horse_prof_data[6], horse_prof_data[7])
                nf.db_diff_insert_race_info(race_info_data[0], race_info_data[1], race_info_data[2])

        # 子プロセスからのスクレイプ失敗通知
        # untracked テーブルに挿入しておく
        elif data[0] == "FAILED":
            if data[1] == "scrape_race_result":
                nf.db_insert_untracked_race_id(data[2])

            elif data[1] == "scrape_horse_result":
                nf.db_insert_untracked_horse_id(data[2])

        # すべての子プロセスの完了確認
        if 0 in children_comp_flg:
            pass
        else:
            break

def scrape_process(parent_queue, child_queue, children_id):
    browser      = private_ini("scraping", "browser")
    mail_address = private_ini("scraping", "mail")
    password     = private_ini("scraping", "pass")

    path_userdata = os.getcwd() + '/' + path_ini("scraping", "path_userdata")
    path_userdata = path_userdata.replace('\\', '/')

    # スクレイピング用driver設定
    arg_list = ['--user-data-dir=' + path_userdata + str(children_id), '--profile-directory=Profile ' + str(children_id), '--disable-logging', '--blink-settings=imagesEnabled=false']


    driver = wf.start_driver(browser, arg_list, True)

    # login(driver, mail_address, password)

    queue = child_queue
    while True:
        data = queue.get()

        # 親プロセスから終了要求受信
        if data[0] == "FIN":
            driver.close()
            break
        
        # REQ 受信
        # スクレイプを行う
        elif data[0] == "REQ":
            children_id, func, id = data[1:]
            if func is None:
                print("!!! func is not defined !!!")
            if id is None:
                print("!!! id is not defined !!!")
            func(queue, [id], driver)

        # スクレイプ完了通知受信 (From func)
        # 次のスクレイプ id の要求を送信してから
        # 結果を親プロセスに送信する
        # この順番により次のジョブがくるまでの間隔が短くなるはず
        elif data[0] == "SUCCESS":
            parent_queue.put(["REQ", children_id])
            parent_queue.put(data)

        # スクレイプ失敗通知受信 (From func)
        # 次のスクレイプ id の要求を送信してから
        # 結果を親プロセスに送信する
        # この順番により次のジョブがくるまでの間隔が短くなるはず
        elif data[0] == "FAILED":
            parent_queue.put(["REQ", children_id])
            parent_queue.put(data)
            
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
        err_msg = 'ログインに失敗した可能性.ログインidとパスワードを確認してください.正しい場合は.netkeiba_scraping.pyのコードを変更してください.'
        raise ValueError(err_msg)
    
####################################################################################

def build_perform_contents(driver, horseID):
    ## 競走成績テーブルの取得
    logger.debug('get result table')
    COL_NAME_TEXT = ['レース名', '日付', '開催', '頭 数', '枠 番', '馬 番', 'オ ッ ズ', '人 気', '着 順', '斤 量', '距離', '馬 場', 'タイム', '着差', '通過', 'ペース', '上り', '賞金']

    # 旧perform_table
    element_table = driver.find_element(By.XPATH, "//*[@class='db_h_race_results nk_tb_common']")
    
    # 表のテキスト取得
    html = element_table.get_attribute('outerHTML')
    dfs = pd.read_html(html, header=0)
    for col in dfs[0].columns:
        if not (col in COL_NAME_TEXT):
            dfs[0].drop(col, axis=1, inplace=True)
    
    # jockey id 取得
    jockey_link_list = re.findall('/jockey/result/recent/[0-9a-zA-Z]{5}', html)
    jockey_link_list = list(map(lambda x: (x.replace("/jockey/result/recent/", '')), jockey_link_list))
    # print("jockey_link_list = ", jockey_link_list)

    # race_id 取得
    race_link_list = re.findall('/race/[0-9a-zA-Z]{12}', html)
    race_link_list = list(map(lambda x: (x.replace("/race/", '')), race_link_list))
    # print("race_link_list = ", race_link_list)

    all_perform_contents = []
    for i in range(len(dfs[0])):
        perform_contents = [0] * 21
        perform_contents[0]     = horseID
        perform_contents[1:2]   = dfs[0].loc[i, '日付':'開催']
        perform_contents[3]     = race_link_list[i]
        perform_contents[4:9]   = dfs[0].loc[i, '頭 数':'着 順']
        perform_contents[10]    = jockey_link_list[i]
        perform_contents[11:19] = dfs[0].loc[i, '斤 量':'賞金']
        perform_contents[20]    = string2grade(dfs[0].loc[i, 'レース名'], dfs[0].loc[i, '距離'])
        all_perform_contents.append(perform_contents)

    return all_perform_contents

####################################################################################   


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
        target_col_hp = [*target_col_hp, "blood_f","blood_ff","blood_fm","blood_m","blood_mf","blood_mm", "horse_id","horse_title","check_flg","retired_flg", "review_cource_left_text", "review_cource_left", "review_cource_right", "review_cource_right_text", "review_distance_left_text", "review_distance_left", "review_distance_right", "review_distance_right_text", "review_style_left_text", "review_style_left", "review_style_right", "review_style_right_text", "review_grow_left_text", "review_grow_left", "review_grow_right", "review_grow_right_text", "review_heavy_left_text", "review_heavy_left", "review_heavy_right", "review_heavy_right_text"] #★順序対応確認
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

        ## 適正レビューテーブルの取得
        logger.debug('get Approproate table')
        app_table = driver.find_element(By.XPATH, "//*[@class='tekisei_table']")
        app_table = app_table.find_elements(By.TAG_NAME, "img")
        app_list = []
        for i in range(5):
            # i:0 コース適性 (芝 <-> ダート)
            # i:1 距離適性 (短い <-> 長い)
            # i:2 脚質 (逃げ <-> 追込)
            # i:3 成長 (早熟 <-> 晩生)
            # i:4 重馬場 (得意 <-> 苦手)
            review_1 = app_table[i * 5 + 0].get_attribute("width") # ゲージ左文字
            review_2 = app_table[i * 5 + 1].get_attribute("width") # ゲージ左
            review_3 = app_table[i * 5 + 2].get_attribute("width") # センターライン(不要)
            review_4 = app_table[i * 5 + 3].get_attribute("width") # ゲージ右
            review_5 = app_table[i * 5 + 4].get_attribute("width") # ゲージ右文字

            app_list.extend([review_1, review_2, review_4, review_5])
        logger.info("app_list = {0}".format(app_list))


        ## 競走成績テーブルの取得
        logger.debug('get result table')
        perform_contents = build_perform_contents(driver, horseID)

        ## 競走成績のデータ取得が成功したかどうかを、通算成績の出走数と競走成績の行数で判定
        if num_entry_race == len(perform_contents):
            check = "1" # OK
        else:
            check = "0" # データ欠損アリ (prof_tableとperform_tableで一致しない)
        
        # 進捗表示
        if (iter_num+1) % progress_notice_cycle == 0:
            logger.info("scrape_horsedata {0} / {1} finished.".format(iter_num+1, len(horseID_list)))

        # target_col_ri
        # target_col_ri =  ['horse_id', 'date', 'venue', 'race_id', 'horse_num', 'post_position', 'horse_number', 'odds', 'fav', 'result', 'jockey_id', 'burden_weight', 'distance', 'course_condition', 'time', 'margin', 'corner_pos', 'pace', 'last_3f', 'prize', 'grade']

        #TODO: 各テーブルに挿入しやすいようにクラスで返すようにする
        yield [prof_contents, blood_list, horseID, horse_title, check, retired, app_list, target_col_hp], [perform_contents, horseID] # [perform_contents, target_col_ri, horseID]
    logger.info("scrape_horsedata comp")


def scrape_racedata(driver, race_id):
    """horseIDを取得する & race情報を得る。レースに出走した馬のリストを返す。
    driver: webdriver
    race_id: 調べるraceID
    """

    # レースページにアクセス
    race_url = "https://db.netkeiba.com/race/{}/".format(race_id)
    logger.debug('access {}'.format(race_url))
    wf.access_page(driver, race_url)

    COL_NAME_TEXT = ["着 順", "枠 番", "タイム", "着差", "馬体重", "賞金 (万円)", "斤量"]
    element_table = driver.find_element(By.XPATH, "//*[@class='race_table_01 nk_tb_common']")

    # 表のHTML取得
    html = element_table.get_attribute('outerHTML')
    dfs = pd.read_html(html, header=0)
    for col in dfs[0].columns:
        if not (col in COL_NAME_TEXT):
            dfs[0].drop(col, axis=1, inplace=True)

    ## race情報の取得・整形と保存 (払い戻しの情報は含まず)
    # レース名、レースデータ1(天候など)、レースデータ2(日付など)  <未補正 文字列>
    race_name = driver.find_element(By.XPATH,"//*[@id='main']/div/div/div/diary_snap/div/div/dl/dd/h1").text
    race_data1 = driver.find_element(By.XPATH,"//*[@id='main']/div/div/div/diary_snap/div/div/dl/dd/p/diary_snap_cut/span").text
    race_data2 = driver.find_element(By.XPATH,"//*[@id='main']/div/div/div/diary_snap/div/div/p").text

    # グレード判定
    grade_str = race_data1.split("/")[0]
    grade = string2grade(race_name, grade_str)

    # horse_id取得
    horse_id_list = re.findall('/horse/[0-9a-zA-Z]{10}', html)
    horse_id_list = list(map(lambda x: (x.replace("/horse/", '')), horse_id_list))

    # Webページの列名をDBの列名に変更
    dfs[0].rename(columns=col_name_dict, inplace=True)
    
    # 共通列追加
    dfs[0]["grade"]      = grade
    dfs[0]["race_name"]  = race_name
    dfs[0]["race_data1"] = race_data1
    dfs[0]["race_data2"] = race_data2
    dfs[0]["race_id"]    = race_id
    dfs[0]["horse_id"]   = horse_id_list
    
    return dfs[0]

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

        print("raceID_list = ", raceID_list)

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
            yield checked_race_id_list

####################################################################################################

def scrape_race_result(queue, race_id_list, driver):
    # race_result テーブルに挿入するデータをスクレイピングしてくる
    # スクレイピング成功時の戻り ["SUCCESS", "scrape_race_result", race_result行]
    # スクレイピング失敗時の戻り ["FAILED" , "scrape_race_result", race_id_list]
    try:
        race_result = scrape_racedata(driver, race_id_list)
        queue.put(["SUCCESS", "scrape_race_result", race_result], block=True)
    except:
        queue.put(["FAILED", "scrape_race_result", race_id_list], block=True)

def scrape_horse_result(queue, horse_id_list, driver):
    # TODO: 必要？
    # checked_list = nf.db_not_retired_list(horse_id_list)
    checked_list = horse_id_list
    try:
        for horse_prof_data, race_info_data in scrape_horsedata(driver, checked_list):
            queue.put(["SUCCESS", "scrape_horse_result", [horse_prof_data, race_info_data]], block=True)
    except:
        queue.put(["FAILED", "scrape_horse_result", checked_list], block=True)

####################################################################################################

if __name__ == "__main__":
    # netkeiba ログイン情報読み込み
    browser      = private_ini("scraping", "browser")
    mail_address = private_ini("scraping", "mail")
    password     = private_ini("scraping", "pass")

    # 並列スクレイピング数
    process_num = int(private_ini("scraping", "process_num"))

    # tmpファイルパス読み込み
    path_tmp = path_ini("common", "path_tmp")

    # 引数パース
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--init', action='store_true', default=False, help='init database and scrape until today')
    parser.add_argument('-d','--db', action='store_true', default=False, help='update database')
    parser.add_argument('-r','--race_id', help='scrape race_id info')
    parser.add_argument('-t','--test', action='store_true', default=False, help='for debug scraping')

    args = parser.parse_args()

    path_userdata = os.getcwd() + '/' + path_ini("scraping", "path_userdata")
    path_userdata = path_userdata.replace('\\', '/')
    print("path_userdata = ", path_userdata)

    # スクレイピング用driver設定
    # プロセス数分のログインセッションを持ったユーザを作成
    # ログインボタンは画像のためここでは画像を読む(フラグなし)
    # for i in range(process_num):
    #     print("process {0} init...".format(i))
    #     # arg_list = ['--single-process', '--headless', '-no-sandbox', '--disable-gpu', '--user-data-dir=C:/Users/hxbdy/AppData/Local/Google/Chrome/User Data', '--profile-directory=Profile 1', '--disable-logging', '--user-agent=hogehoge']
    #     arg_list = ['--user-data-dir=' + path_userdata + str(i), '--profile-directory=Profile '+str(i), '--disable-logging']
    #     driver = wf.start_driver(browser, arg_list, False)
    #     login(driver, mail_address, password)
    #     driver.close()


    # DB初期化
    if args.init:
        start = "198601"
        end   = "198602"
        grade = "OP"
        race_id = []
        arg_list = ['--user-data-dir=' + path_userdata + str(0), '--profile-directory=Profile 0', '--disable-logging']
        driver = wf.start_driver(browser, arg_list, False)
        for race_id_list in regist_scrape_race_id(driver, start, end, grade):
            race_id.extend(race_id_list)
        queue = Queue()
        driver.close()
        main_process(queue, race_id, process_num)

    # 定期的なDBアップデート
    # 1ヶ月間隔更新前提
    elif args.db:
        pass
    elif args.race_id:
        for horse_prof_data, race_info_data in scrape_horsedata(driver, ["2019102879"]):
            print(horse_prof_data)
            print(race_info_data)
    elif args.test:
        # debug
        arg_list = ['--user-data-dir=' + path_userdata + str(0), '--profile-directory=Profile 0', '--disable-logging', '--blink-settings=imagesEnabled=false']
        driver = wf.start_driver(browser, arg_list, True)

        time_sta = time.perf_counter()
        table = scrape_racedata(driver, "198601010809")
        time_end = time.perf_counter()
        logger.info("scraping time = {0} [sec]".format(time_end - time_sta))

        print(table)
        driver.close()

    else:
        logger.error("read usage: netkeiba_scraping.py -h")
