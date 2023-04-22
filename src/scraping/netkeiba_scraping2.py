# マルチプロセスで馬の情報、レース情報をデータベースへ保存する
# 1. スクレイプするレースIDは直列で取得する(untracked_race_idキューにエンキューする)
# 2. private.iniで設定してあるマルチプロセス数分ドライバを作成して、スクレイプする
# 2.1. 並列で動作するプロセスは、スクレイププロセス + DB制御プロセス
# 2.2. スクレイププロセスは、レース情報をスクレイプするか馬情報をスクレイプするかはキューのたまり具合で判断する

# 残件
# 1. 取得に失敗したIDを再度取得チャレンジするオプションの追加
# 2. ログがフォーマット通り出力されない問題の対処

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
import numpy as np
import psutil

import webdriver_functions as wf
from NetkeibaDB_IF import NetkeibaDB_IF
from file_path_mgr import path_ini, private_ini
from debug         import stream_hdl, file_hdl

from deepLearning_common import write_RaceInfo
from RaceInfo      import RaceInfo

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("output"))

# プロセス優先度設定(通常以上にはしないこと)
# 通常以下 : psutil.BELOW_NORMAL_PRIORITY_CLASS
# 通常 : psutil.NORMAL_PRIORITY_CLASS
psutil.Process().nice(psutil.NORMAL_PRIORITY_CLASS)

####################################################################################

# netkeiba上の列名とデータベース上の名前をつなぐ辞書
# (空白文字揺れも含む)
col_name_dict = {
    # 揺れあり
    "枠 番":"post_position", "枠番":"post_position",
    "馬 番":"horse_number", "馬番":"horse_number",
    "着 順":"result","着順":"result",
    "斤量":"burden_weight", "斤 量":"burden_weight",
    "オッズ":"odds","オ ッ ズ":"odds",
    "賞金":"prize", "賞金 (万円)":"prize", "賞金":"prize", "賞金(万円)":"prize",
    "頭 数":"horse_num", "頭数":"horse_num",
    "人 気":"fav", "人気":"fav",
    "馬 場":"course_condition", "馬場":"course_condition",
    # 揺れなし
    "距離":"distance", "タイム":"time", "着差":"margin", "レース名":"race_id",
    "騎手":"jockey_id", "通過":"corner_pos", "ペース":"pace",
    "上り":"last_3f", "馬名":"horse_id", "馬体重":"horse_weight",
    "日付":"date", "開催":"venue",
    "生年月日":"bod", "馬主":"owner", "生産者":"producer", "産地":"area", "セリ取引価格":"auction_price",
    "獲得賞金":"earned", "通算成績":"lifetime_record", "主な勝鞍":"main_winner", "近親馬":"relative", "調教師":"trainer"
}

# 曜日辞書
# date.weekday()で取得できる曜日と文字列の対応
weekday = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"}

# race_info テーブル
race_info_col_name_dict = (
    "date","venue","horse_num","post_position","horse_number","odds","fav","result","jockey_id",
    "burden_weight","distance","course_condition","time","margin","corner_pos","pace","last_3f","prize",
)

# horse_prof テーブル
horse_prof_col_name_dict = (
    "bod","trainer","owner","producer","area","auction_price","earned","lifetime_record","main_winner","relative",
)

# race_result テーブル
race_result_col_name_dict = (
    "post_position", "burden_weight", "burden_weight", "time", "margin", "horse_weight", "prize", "prize", "result"
)

####################################################################################

def update_database_predict(driver, horseID_list):
    """レース直前に、レース結果の予想に必要なデータのみを集める。
    レースに出走する馬に対して、scrape_horsedataを実行し、race_infoとhorse_profを更新する。
    driver: webdriver
    horseID_list: レースに出走する馬のhorse idのリスト
    """

    nf = NetkeibaDB_IF("ROM")

    for horse_id in horseID_list:
        prof, race_info = scrape_horsedata(driver, horse_id)
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

    # 何レース目かはrace_idの末尾2文字
    # 自動投票に必要
    raceInfo.race_no = raceID[-2:] + 'R'
    
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
    venue = racedata02[1].text            # '中山'
    prize_str = racedata02[-1].text       # '本賞金:1840,740,460,280,184万円'
    raceInfo.prize = re.findall(r"\d+", prize_str) # ['1840', '740', '460', '280', '184']

    # 開催地 + 曜日 表記
    # 自動投票に必要
    raceInfo.venue = venue + '(' + weekday[raceInfo.date.weekday()] + ')'

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
    
    print("開催地")
    print(raceInfo.venue)
    print("レース")
    print(raceInfo.race_no)
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

def main_process(untracked_race_id_list, children_num, roll):
    children_process  = []
    children_queue    = []

    # プロセス終了FIN送信のタイミングでセットする
    children_comp_flg = [0] * children_num

    queue = Queue()
    
    # スクレイピング対象のidを準備
    untracked_race_id_queue  = deque(untracked_race_id_list)
    untracked_horse_id_queue = deque()

    # 前回 FAILED した id を再度スクレイプしてみる
    if roll:
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

    # メモリ溢れ対策
    MEM_LIMIT_WAIT_SEC = 100
    mem_limit_cnt = 0

    while True:
        data = queue.get()

        # DB制御キュー溢れ対策
        # DB制御キューを捌けさせて、メモリが空くのを待つ
        # 一定時間待っても改善しない場合は強制終了する
        mem = psutil.virtual_memory()
        while mem.percent > 90.0:
            # 待ちの数を10以下になるまで待つ
            # 待ってもメモリの使用率が改善しない場合は一定時間経過後に強制終了
            print("mem {0}% used ! queue size = {1} | wait {2}/{3}".format(mem.percent, db_queue.qsize(), mem_limit_cnt, MEM_LIMIT_WAIT_SEC))
            if db_queue.qsize() > 10:
                time.sleep(1)
            else:
                if mem_limit_cnt > MEM_LIMIT_WAIT_SEC:
                    # 強制終了
                    # スクレイププロセスに終了要求送信
                    print("scrape imm FIN send")
                    for i in range(children_num):
                        children_queue[i].put(["FIN", i, None, None])
                        children_comp_flg[children_id] = 1
                    # スクレイププロセス終了待ち
                    # メインプロセスが先に終了してしまう時のデッドロック回避
                    for i in range(children_num):
                        children_process[i].join(timeout = 90)
                    # untracked キューで待っていたidを払い出し。DBに保存しておく
                    print("scrape_race_result send")
                    while len(untracked_race_id_queue) > 0:
                        race_id = untracked_race_id_queue.pop()
                        db_queue.put(["FAILED_INSERT", "scrape_race_result", race_id])
                    print("scrape_horse_result send")
                    while len(untracked_horse_id_queue) > 0:
                        horse_id = untracked_horse_id_queue.pop()
                        db_queue.put(["FAILED_INSERT", "scrape_horse_result", horse_id])
                    print("db_queue FIN send")
                    db_queue.put(["FIN"])
                    # DB制御プロセス終了待ち
                    # メインプロセスが先に終了してしまう時のデッドロック回避
                    child_db_process.join(timeout = 90)
                else:
                    mem_limit_cnt += 1
                    time.sleep(1)
        mem_limit_cnt = 0

        # 進捗確認
        logger.info("untracked_race_id_queue:{0}".format(len(untracked_race_id_queue)))
        logger.info("untracked_horse_id_queue:{0}".format(len(untracked_horse_id_queue)))

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
            print("children_comp_flg = ", children_comp_flg)
        else:
            break

    # DB制御プロセス終了
    db_queue.put(["FIN"])
    print("snd db_queue FIN")

    # 子プロセス終了待ち
    # メインプロセスが先に終了してしまう時のデッドロック回避
    for i in range(children_num):
        children_process[i].join(timeout = 90)

    # 終了したかの確認
    # 終了していない場合(joinタイムアウト発生)、子プロセスが終了できなくなっているため強制終了する
    child_db_process.kill()
    for i in range(children_num):
        if(children_process[i].is_alive()):
            logger.critical('failed to terminate scrape process !! force kill ID:{0}'.format(i))
            children_process[i].kill()

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

    queue :Queue= child_queue
    
    while True:
        try:
            data = queue.get(timeout=60)
        except Exception as e:
            print("Exception", e.args)
            # スクレイピングに60 sec以上かかった
            # 失敗としてdriverは再起動して次に行く
            print("scrape timeout !!!")
            print("-> TIMEOUT FAILED REQ id =", children_id)

            # reboot driver
            driver.close()
            driver = wf.start_driver(browser, arg_list, True)

            parent_queue.put(["REQ", children_id])

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
    print("scrape_process fin id:", children_id)
            
def db_process(parent_queue, child_queue):
    nf = NetkeibaDB_IF("RAM")
    queue = child_queue
    while True:
        data = queue.get()

        # 進捗確認
        logger.info("db_ctrl_queue:{0}".format(queue.qsize()))

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
    print("db_process fin")

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

    element_table = driver.find_element(By.XPATH, "//*[@class='db_h_race_results nk_tb_common']")
    
    # 表のテキスト取得
    html = element_table.get_attribute('outerHTML')
    dfs = pd.read_html(html, header=0)

    # Webページの列名をDBの列名に変更
    dfs[0].rename(columns=col_name_dict, inplace=True)

    # grade 取得
    grade_list = []
    for i in range(len(dfs[0])):
        grade = string2grade(dfs[0].loc[i, 'race_id'], dfs[0].loc[i, 'distance'])
        grade_list.append(grade)

    # 不要な列削除
    for col in dfs[0].columns:
        if not (col in race_info_col_name_dict):
            dfs[0].drop(col, axis=1, inplace=True)

    # jockey id 取得
    # 騎手列の名前をtitleとしたリンクがあるなら騎手idが存在する
    jockey_link_list = []
    for jockey_name in dfs[0][col_name_dict["騎手"]]:
        # 騎手名のtitleタグがあるか確認
        title_jockey_id = 'title="{0}"'.format(jockey_name)
        jockey_id = re.search('/jockey/result/recent/[0-9a-zA-Z]{5}/" ' + title_jockey_id, html)
        # あるならidを登録
        if jockey_id:
            jockey_id = jockey_id.group()
            jockey_id = jockey_id.replace("/jockey/result/recent/", '')
            jockey_id = jockey_id.replace('/" '+title_jockey_id, '')
        else:
            jockey_id = np.nan
        jockey_link_list.append(jockey_id)

    # race_id 取得
    race_link_list = re.findall('/race/[0-9a-zA-Z]{12}', html)
    race_link_list = list(map(lambda x: (x.replace("/race/", '')), race_link_list))
    # print("race_link_list = ", race_link_list)

    dfs[0]["horse_id"] = horseID
    dfs[0]["race_id"] = race_link_list
    dfs[0]["jockey_id"] = jockey_link_list
    dfs[0]["grade"] = grade_list

    return dfs[0]

####################################################################################   

def update_jockey_info(lower_year, upper_year):
    """jockey_infoテーブルの更新
    開始年から終了年までの各年で、騎手の騎乗回数をカウントしてテーブルを更新。
    騎乗回数はrace_infoテーブルから計上する。
    lower_year: 開始年
    upper_year: 終了年
    """
    nf = NetkeibaDB_IF("RAM")

    df = pd.DataFrame(columns=["jockey_id", "year", "num"])

    for year in range(lower_year, upper_year+1):
        year = str(year)
        year0 = year + "00000000"
        year1 = year + "99999999"

        # (year)年に騎乗した騎手のリスト
        jockey_list = nf.db_race_info_jockey_list(year0, year1)
        
        logger.info("year {}, #jockey = {}".format(year, len(jockey_list)))

        for jockey_id in jockey_list:
            # 騎乗回数のカウント
            cnt = nf.db_race_info_jockey_cnt(jockey_id, year0, year1)
            insert_dict = {"jockey_id":jockey_id, "year":year, "num":cnt}
            df = df.append(insert_dict, ignore_index=True)
    
    # dbの更新
    nf.db_insert_pandas(df, "jockey_info")

def scrape_horsedata(driver, horseID):
    """馬のデータを取得して保存する
    driver: webdriver
    horseID: 調べるhorseID
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

    # Webページの列名をDBの列名に変更
    prof.rename(columns = col_name_dict, inplace=True)

    # 不要な列は削除する
    for col in prof.columns:
        if not (col in horse_prof_col_name_dict):
            prof.drop(col, axis=1, inplace=True)

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

    trainer = re.search('/trainer/[0-9a-zA-Z]{5}', html)
    if trainer:
        trainer = trainer.group()
        trainer = trainer.replace("/trainer/", "")
    else:
        trainer = np.nan

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
    # logger.info("app_list = {0}".format(app_list))


    ## 競走成績テーブルの取得
    logger.debug('get result table')
    race_info = build_perform_contents(driver, horseID)

    ## 競走成績のデータ取得が成功したかどうかを、通算成績の出走数と競走成績の行数で判定
    if num_entry_race == len(race_info):
        check = "1" # OK
    else:
        check = "0" # データ欠損アリ (prof_tableとperform_tableで一致しない)

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

    element_table = driver.find_element(By.XPATH, "//*[@class='race_table_01 nk_tb_common']")

    # 表のHTML取得
    html = element_table.get_attribute('outerHTML')
    dfs = pd.read_html(html, header=0)

    # Webページの列名をDBの列名に変更
    dfs[0].rename(columns=col_name_dict, inplace=True)

    # テーブルに挿入しない列を削除
    for col in dfs[0].columns:
        if not (col in race_result_col_name_dict):
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

            # フィルタ処理を行わない
            # checked_race_id_list = race_id_list

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
    except Exception as e:
        print("Exception", e.args)
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

    # 並列スクレイピング数読み込み
    process_num = int(private_ini("scraping", "process_num"))

    # 引数パース
    parser = argparse.ArgumentParser()
    parser.add_argument('--init', action='store_true', default=False, help='init database and scrape until today') # DB初期化
    parser.add_argument('--db', action='store_true', default=False, help='update database')                        # 今日から一ヶ月前までのレースをスクレイピング
    parser.add_argument('--race_id', help='scrape race_id info')                                                   # 特定のレースのみスクレイピング
    parser.add_argument('--debug', action='store_true', default=False, help='for debug scraping')                  # デバッグ用
    parser.add_argument('--skip_login', action='store_true', default=False, help='skip login')                     # netkeibaへのログイン作業をスキップする
    parser.add_argument('--skip_untracked', action='store_true', default=False, help='retry')                      # 前回スクレイピングで取得に失敗したページの再取得をスキップする
    parser.add_argument('--untracked', action='store_true', default=False, help='retry')                           # 前回スクレイピングで取得に失敗したページの再取得をのみを実行する

    args = parser.parse_args()

    # スクレイピングに使うブラウザのダミーユーザデータの保存場所を用意
    path_userdata = os.getcwd() + '/' + path_ini("scraping", "path_userdata")
    path_userdata = path_userdata.replace('\\', '/')
    print("path_userdata = ", path_userdata)

    # スクレイピング用driver設定
    # プロセス数分のログインセッションを持ったダミーユーザを作成
    # ログインボタンは画像のためここでは画像を読む
    if not args.skip_login:
        for i in range(process_num):
            print("process {0} init...".format(i))
            arg_list = ['--user-data-dir=' + path_userdata + str(i), '--profile-directory=Profile '+str(i), '--disable-logging']
            driver = wf.start_driver(browser, arg_list, False)
            login(driver, mail_address, password)
            driver.quit()

    # DB初期化
    if args.init:
        # スクレイピング範囲は1986年1月から今日まで
        start = "198601"
        end = datetime.datetime.now().strftime("%Y%m")

        # すべてのグレードを対象とする
        grade = "OP"

        race_id = []
        arg_list = ['--user-data-dir=' + path_userdata + str(0), '--profile-directory=Profile 0', '--disable-logging']
        driver = wf.start_driver(browser, arg_list, False)
        for race_id_list in regist_scrape_race_id(driver, start, end, grade):
            race_id.extend(race_id_list)
        driver.quit()
        main_process(race_id, process_num, args.skip_untracked)
        
        # jockey_infoテーブルアップデート
        update_jockey_info(int(start[:-2]), int(end[:-2]))

        # インデックスを貼る
        nf = NetkeibaDB_IF("ROM", read_only=False)
        nf.interface_make_index()

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
        driver.quit()
        main_process(race_id, process_num, args.skip_untracked)

        # jockey_infoテーブルアップデート
        update_jockey_info(int(start[:-2]), int(end[:-2]))

    # 当日予想
    elif args.race_id:
        arg_list = ['--user-data-dir=' + path_userdata + str(0), '--profile-directory=Profile 0', '--disable-logging', '--blink-settings=imagesEnabled=false']
        driver = wf.start_driver(browser, arg_list, False)

        # 当日予想したいレースIDから馬の情報をコンソール出力
        a = scrape_race_today(driver, args.race_id)

        # 出走する馬のDB情報をアップデート
        update_database_predict(driver, a.horse_id)

        # 推測用に取得したレース情報を一時保存
        write_RaceInfo(a)

        driver.quit()

    elif args.untracked:
        main_process([], process_num, True)
        # jockey_infoテーブルアップデート
        update_jockey_info(1986, int(datetime.datetime.now().strftime("%Y")))

    elif args.debug:
        # debug用引数
        arg_list = ['--user-data-dir=' + path_userdata + str(0), '--profile-directory=Profile 0', '--disable-logging', '--blink-settings=imagesEnabled=false']
        driver = wf.start_driver(browser, arg_list, False)
        prof, race_info = scrape_horsedata(driver, "2008190006")
        print("prof = ", prof)
        print("race_info = ", race_info)
        driver.close()

    else:
        logger.error("read usage: netkeiba_scraping.py -h")
