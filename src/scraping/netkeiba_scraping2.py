import re
import os
import time
import logging
import argparse
import datetime
import pickle
from dateutil.relativedelta import relativedelta
from multiprocessing        import Process, Queue
from collections            import deque

from selenium.webdriver.common.by import By
import pandas as pd

import webdriver_functions as wf
from NetkeibaDB_IF import NetkeibaDB_IF
from file_path_mgr import path_ini, private_ini
from debug         import stream_hdl, file_hdl
from RaceInfo      import RaceInfo

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("output"))

####################################################################################

# netkeiba上の列名とデータベース上の名前をつなぐ辞書
col_name_dict = {
    "日付":"date", "開催":"venue", "頭 数":"horse_num", "枠 番":"post_position", \
    "馬 番":"horse_number", "オッズ":"odds","オ ッ ズ":"odds", "人 気":"fav", "着 順":"result", "斤量":"burden_weight", "斤 量":"burden_weight", \
    "距離":"distance","馬 場":"course_condition", "タイム":"time", "着差":"margin", "賞金":"prize", \
    "レース名":"race_id", "騎手":"jockey_id", "通過":"corner_pos", "ペース":"pace", \
    "上り":"last_3f", "馬名":"horse_id", "馬体重":"horse_weight", "賞金 (万円)":"prize", "賞金":"prize", \
    "生年月日":"bod", "馬主":"owner", "生産者":"producer", "産地":"area", "セリ取引価格":"auction_price", \
    "獲得賞金":"earned", "通算成績":"lifetime_record", "主な勝鞍":"main_winner", "近親馬":"relative", "調教師":"trainer"
}

####################################################################################

# TODO: マージまでの残件
# 1. jockeyテーブル更新
# 2. DBのインデックス貼り付けを自動でやる
# 3. DBの初期化、当日の予測、定期更新ができることを確認する
# 4. エンコードを実行し互換性を保持できていることを確認する

def update_database_predict(driver, horseID_list):
    """レース直前に、レース結果の予想に必要なデータのみを集める。
    レースに出走する馬に対して、scrape_horsedataを実行し、race_infoとhorse_profを更新する。
    driver: webdriver
    horseID_list: レースに出走する馬のhorse idのリスト
    """
    prof, race_info = scrape_horsedata(driver, horseID_list)

    nf = NetkeibaDB_IF("ROM")
    nf.db_insert_pandas(prof, "horse_prof")
    nf.db_insert_pandas(race_info, "race_info")

    #reconfirm_check()
    logger.info("update_horsedata_only comp")

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

    COL_NAME_TEXT = ["枠", "馬番", "斤量", "馬体重(増減)"]
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
    raceInfo.horse_weight = list(map(lambda x: x[5], contents))
    
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
    print("馬体重")
    print(raceInfo.horse_weight)
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

def main_process(untracked_race_id_list, children_num):
    children_process  = []
    children_queue    = []
    children_comp_flg = [0] * children_num

    queue = Queue()
    
    # スクレイピング対象のidを準備
    untracked_race_id_queue  = deque(untracked_race_id_list)
    untracked_horse_id_queue = deque()

    # 前回 FAILED した id があればエンキューしておく
    nf = NetkeibaDB_IF("ROM")
    untracked_race_id_queue.extend(nf.db_pop_untracked_race_id())
    untracked_horse_id_queue.extend(nf.db_pop_untracked_horse_id())
    del nf

    # スクレイププロセス起動
    # REQ メッセージをエンキュー
    for i in range(children_num):
        children_queue.append(Queue())
        children_process.append(Process(target=scrape_process, args=(queue, children_queue[-1], i)))
        children_process[-1].start()
        queue.put(["REQ", i])

    # DB制御プロセス起動
    db_queue = Queue()
    child_db_process = Process(target=db_process, args=(queue, db_queue))
    child_db_process.start()

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
                race_result, horse_id_list = data[2]
                print("<- rcv SUCCESS scrape_race_result")

                db_queue.put(["SUCCESS_UPSERT", race_result, "race_result"])
                # horse_idのスクレイピング依頼
                untracked_horse_id_queue.extend(horse_id_list)

            # 馬のスクレイプ完了通知受信
            # horse_prof / race_info テーブルの更新
            elif data[1] == "scrape_horse_result":
                horse_prof, race_info = data[2]
                print("<- rcv SUCCESS scrape_horse_result")

                db_queue.put(["SUCCESS_UPSERT", horse_prof, "horse_prof"])
                db_queue.put(["SUCCESS_UPSERT", race_info, "race_info"])

        # 子プロセスからのスクレイプ失敗通知
        # untracked テーブルに挿入しておく
        elif data[0] == "FAILED":
            if data[1] == "scrape_race_result":
                print("<- rcv FAILED scrape_race_result")
                db_queue.put(["FAILED_INSERT", "scrape_race_result", data[2]])

            elif data[1] == "scrape_horse_result":
                print("<- rcv FAILED scrape_horse_result")
                db_queue.put(["FAILED_INSERT", "scrape_horse_result", data[2]])

        # すべての子プロセスの完了確認
        if 0 in children_comp_flg:
            pass
            # print("children_comp_flg = ", children_comp_flg)
        else:
            break

    # DB制御プロセス終了
    db_queue.put(["FIN"])
    print("snd db_queue FIN")

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
            print("-> SUCCESS REQ id =", children_id)
            parent_queue.put(["REQ", children_id])
            parent_queue.put(data)

        # スクレイプ失敗通知受信 (From func)
        # 次のスクレイプ id の要求を送信してから
        # 結果を親プロセスに送信する
        # この順番により次のジョブがくるまでの間隔が短くなるはず
        elif data[0] == "FAILED":
            print("-> FAILED REQ id =", children_id)
            parent_queue.put(["REQ", children_id])
            parent_queue.put(data)
            
def db_process(parent_queue, child_queue):
    nf = NetkeibaDB_IF("ROM")
    queue = child_queue
    while True:
        data = queue.get()

        # 親プロセスから終了要求受信
        if data[0] == "FIN":
            break

        elif data[0] == "SUCCESS_UPSERT":
            df = data[1]
            table_name = data[2]
            nf.db_insert_pandas(df, table_name)

        elif data[0] == "FAILED_INSERT":
            if data[1]=="scrape_race_result":
                nf.db_insert_untracked_race_id(data[2])
            elif data[1]=="scrape_horse_result":
                nf.db_insert_untracked_horse_id(data[2])

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

    # grade 取得
    grade_list = []
    for i in range(len(dfs[0])):
        grade = string2grade(dfs[0].loc[i, 'レース名'], dfs[0].loc[i, '距離'])
        grade_list.append(grade)

    dfs[0].rename(columns=col_name_dict, inplace=True)

    dfs[0]["horse_id"] = horseID
    dfs[0]["race_id"] = race_link_list
    dfs[0]["jockey_id"] = jockey_link_list
    dfs[0]["grade"] = grade_list

    return dfs[0]

####################################################################################   


def scrape_horsedata(driver, horseID):
    """馬のデータを取得して保存する
    driver: webdriver
    horseID_list: 調べるhorseIDのリスト
    """
    ## 以下保留事項
    # 外国から参加してきた馬はどう処理するのか

    ## 馬のページにアクセス
    horse_url = "https://db.netkeiba.com/horse/{}/".format(horseID)
    logger.debug('access {}'.format(horse_url))
    wf.access_page(driver, horse_url)

    html = driver.page_source
    dfs = pd.read_html(html)
    
    # _ = dfs[0]
    prof = dfs[1]
    # parent = dfs[2]
    # _ = dfs[3]
    # _ = dfs[4]
    # _ = dfs[5]


    # 転置
    prof = prof.T
        
    # 1行目を列名にする
    prof.columns = prof.iloc[0]
    prof = prof.reindex(prof.index.drop(0))
        
    ## 馬名，英名，抹消/現役，牡牝，毛の色
    # 'コントレイル\nContrail\n抹消\u3000牡\u3000青鹿毛'
    horse_title = driver.find_element(By.CLASS_NAME, "horse_title").text
    # 引退馬判定 (現役:0, 引退:1)
    if "抹消" in horse_title:
        prof["retired_flg"] = "1"
    else:
        prof["retired_flg"] = "0"

    ## プロフィールテーブルの取得
    logger.debug('get profile table')
    trainer = re.findall('/trainer/[0-9a-zA-Z]{5}', html)[0]
    trainer = trainer.replace("/trainer/", "")

    num_entry_race = re.findall('\d+戦\d+勝', html)[0]
    num_entry_race = int(num_entry_race[:num_entry_race.find("戦")])

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
    race_info = build_perform_contents(driver, horseID)

    ## 競走成績のデータ取得が成功したかどうかを、通算成績の出走数と競走成績の行数で判定
    if num_entry_race == len(race_info):
        check = "1" # OK
    else:
        check = "0" # データ欠損アリ (prof_tableとperform_tableで一致しない)

    # horse_prof_data, race_info_data
    prof.rename(columns = col_name_dict, inplace=True)

    prof["blood_f" ] = blood_list[0]
    prof["blood_ff"] = blood_list[1]
    prof["blood_fm"] = blood_list[2]
    prof["blood_m" ] = blood_list[3]
    prof["blood_mf"] = blood_list[4]
    prof["blood_mm"] = blood_list[5]

    prof["horse_id"] = horseID
    prof["horse_title"] = horse_title
    prof["check_flg"] = check

    prof["review_cource_left_text"]    = app_list[0]
    prof["review_cource_left"]         = app_list[1]
    prof["review_cource_right"]        = app_list[2]
    prof["review_cource_right_text"]   = app_list[3]
    prof["review_distance_left_text"]  = app_list[4]
    prof["review_distance_left"]       = app_list[5]
    prof["review_distance_right"]      = app_list[6]
    prof["review_distance_right_text"] = app_list[7]
    prof["review_style_left_text"]     = app_list[8]
    prof["review_style_left"]          = app_list[9]
    prof["review_style_right"]         = app_list[10]
    prof["review_style_right_text"]    = app_list[11]
    prof["review_grow_left_text"]      = app_list[12]
    prof["review_grow_left"]           = app_list[13]
    prof["review_grow_right"]          = app_list[14]
    prof["review_grow_right_text"]     = app_list[15]
    prof["review_heavy_left_text"]     = app_list[16]
    prof["review_heavy_left"]          = app_list[17]
    prof["review_heavy_right"]         = app_list[18]
    prof["review_heavy_right_text"]    = app_list[19]
        
    return prof, race_info


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
    # スクレイピング成功時の戻り ["SUCCESS", "scrape_race_result", [race_result, horse_id_list]]
    # スクレイピング失敗時の戻り ["FAILED" , "scrape_race_result", race_id_list]
    try:
        for race_id in race_id_list:
            race_result :pd= scrape_racedata(driver, race_id)

            # race_result から horse_id のみ取り出しておく
            # (次段の horse_id スクレイピング対象のため)
            queue.put(["SUCCESS", "scrape_race_result", [race_result, race_result["horse_id"]]], block=True)
    except:
        queue.put(["FAILED", "scrape_race_result", race_id_list], block=True)

def scrape_horse_result(queue, horse_id_list, driver):
    # TODO: 必要？
    # checked_list = nf.db_not_retired_list(horse_id_list)
    checked_list = horse_id_list
    try:
        for race_id in checked_list:
            horse_prof_data, race_info_data = scrape_horsedata(driver, race_id)
            queue.put(["SUCCESS", "scrape_horse_result", [horse_prof_data, race_info_data]], block=True)
    except Exception as e:
        print("Exception", e.args)
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
    for i in range(process_num):
        print("process {0} init...".format(i))
        arg_list = ['--user-data-dir=' + path_userdata + str(i), '--profile-directory=Profile '+str(i), '--disable-logging']
        driver = wf.start_driver(browser, arg_list, False)
        login(driver, mail_address, password)
        driver.close()

    # DB初期化
    if args.init:
        start = "198601"
        end   = datetime.datetime.now().strftime("%Y%m")
        grade = "OP"
        race_id = []
        arg_list = ['--user-data-dir=' + path_userdata + str(0), '--profile-directory=Profile 0', '--disable-logging']
        driver = wf.start_driver(browser, arg_list, False)
        for race_id_list in regist_scrape_race_id(driver, start, end, grade):
            race_id.extend(race_id_list)
        driver.close()
        main_process(race_id, process_num)

    # 定期的なDBアップデート
    # 1ヶ月間隔更新
    elif args.db:
        end = datetime.datetime.now()
        start = end - relativedelta(months=1)

        end = end.strftime("%Y%m")
        start = start.strftime("%Y%m")
        
        grade = "OP"
        race_id = []
        arg_list = ['--user-data-dir=' + path_userdata + str(0), '--profile-directory=Profile 0', '--disable-logging']
        driver = wf.start_driver(browser, arg_list, False)
        for race_id_list in regist_scrape_race_id(driver, start, end, grade):
            race_id.extend(race_id_list)
        driver.close()
        main_process(race_id, process_num)

    # 当日予想
    elif args.race_id:
        arg_list = ['--user-data-dir=' + path_userdata + str(0), '--profile-directory=Profile 0', '--disable-logging', '--blink-settings=imagesEnabled=false']
        driver = wf.start_driver(browser, arg_list, True)

        # 当日予想したいレースIDから馬の情報をコンソール出力
        a = scrape_race_today(driver, args.race_id)

        # 出走する馬のDB情報をアップデート
        update_database_predict(driver, a.horse_id)

        # 推測用に取得したレース情報を一時保存
        with open(path_tmp, 'wb') as f:
            pickle.dump(a, f)

        driver.close()

    elif args.test:
        # debug
        pass

    else:
        logger.error("read usage: netkeiba_scraping.py -h")
