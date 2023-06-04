from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

import re
import os
import time
import argparse
import datetime
from dateutil.relativedelta import relativedelta
from multiprocessing        import Process, Queue
from collections            import deque

import selenium
from selenium.webdriver.common.by import By
import pandas as pd
import numpy as np
import psutil

import webdriver_functions as wf
from NetkeibaDB_IF import NetkeibaDB_IF
from file_path_mgr import path_ini, private_ini

from deepLearning_common import write_RaceInfo
from RaceInfo      import RaceInfo

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

def url2ID(url, search):
    # urlからsearchの1つ下の階層の文字列を返す
    dom = url.split('/')
    if search in dom:
        return dom[dom.index(search) + 1]
    logger.critical("{0} is not found in {1}".format(search, url))

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

def get_race_id_list_from_search_result(driver):
    """レース検索結果画面からrace_idリストを作成する
    次ページ以降も取得する"""

    raceID_list = []
    # 次のページリンクをクリックできる限り無限ループ
    while True:
        ## 画面遷移後
        # raceIDをレース名のURLから取得
        # 5列目のデータ全部
        race_column_html = driver.find_elements(By.XPATH, "//*[@class='nk_tb_common race_table_01']/tbody/tr/td[5]")
        
        # race_id 取得
        for i in range(len(race_column_html)):
            race_url_str = race_column_html[i].find_element(By.TAG_NAME,"a").get_attribute("href")
            raceID_list.append(race_url_str)

        # 次ページへ遷移する
        # 「次」リンクにhrefがあればクリックする
        # 無ければexceptするので終了する
        page_links = driver.find_elements(By.TAG_NAME, "li")
        for page_link in page_links:
            if page_link.text == "次":
                try:
                    link = page_link.find_element(By.TAG_NAME, "a").get_attribute("href")
                    logger.debug("href = {}".format(link))
                    if link is not None:
                        wf.click_button_class(driver, "CSS3_Icon_R")
                    break
                except:
                    return raceID_list
            
        time.sleep(1)
    return raceID_list





def scrape_horse_id_list(d):
    driver = d["driver"]
    element_table = driver.find_element(By.XPATH, "//*[@class='race_table_01 nk_tb_common']")
    html = element_table.get_attribute('outerHTML')
    # horse_idを含むURL取得
    horse_id_list_url = re.findall('/horse/[0-9a-zA-Z]{10}', html)
    # horse_idのみ切り取ったリスト
    # horse_id_list = list(map(lambda x: (x.replace("/horse/", '')), horse_id_list_url))
    return ("scraping", horse_id_list_url, scrape_horse_prof, {}),

def scrape_race_result(d):
    """horseIDを取得する & race情報を得る。レースに出走した馬のリストを返す。
    driver: webdriver
    race_id: 調べるraceID
    """
    driver = d["driver"]

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
    horse_id_list_url = list(map(lambda x: "https://db.netkeiba.com/horse/" + x, horse_id_list))
    
    # 共通列追加
    dfs[0]["grade"]      = grade
    dfs[0]["race_name"]  = race_name
    dfs[0]["race_data1"] = race_data1
    dfs[0]["race_data2"] = race_data2
    dfs[0]["race_id"]    = url2ID(driver.current_url, "race")
    dfs[0]["horse_id"]   = horse_id_list

    if d["lan"]:
        return ("db", dfs[0], "race_result"), #("scraping", horse_id_list_url, scrape_horse_prof, {}), ("scraping", horse_id_list_url, build_perform_contents, {})
    else:
        return ("db", dfs[0], "race_result"), ("scraping", horse_id_list_url, scrape_horse_prof, {}), ("scraping", horse_id_list_url, build_perform_contents, {}) # ("scraping", horse_id_list_url, html_save, {}),

def scrape_raceID(d):
    """start_YYMM から end_YYMM までの芝・ダートレースのraceIDを取得する
    driver: webdriver
    start_YYMM: 取得開始年月(1986年以降推奨) <例> "198601" (1986年1月)
    end_YYMM: 取得終了年月(1986年以降推奨) <例> "198601" (1986年1月)
    race_grade: 取得するグレードのリスト 1: G1, 2: G2, 3: G3, 4: OP以上全て, 5: ALL
    """
    driver     = d["driver"]
    start_YYMM = d["start_YYMM"]
    end_YYMM   = d["end_YYMM"]
    race_grade = d["race_grade"]

    try:
        head = datetime.datetime.strptime(start_YYMM, '%Y%m')
        tail = datetime.datetime.strptime(end_YYMM, '%Y%m')
    except:
        logger.critical('invalid year_month[0] = {0}, year_month[1] = {1}'.format(start_YYMM, end_YYMM))
        raise ValueError('年月指定の値が不適切. 6桁で指定する.')
    
    # 期間内のレースIDを取得する
    raceID_list = []
    while head <= tail:
        # head 月から (head+2) 月までのレースを検索
        # 指定範囲を一度にスクレイピングしないのは
        # 通信失敗時のロールバックを抑えるためと検索結果を1ページ(100件)以内に抑えるため
        ptr = head + relativedelta(months = 2)
        if ptr > tail:
            ptr = tail
        
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
        # グレードの指定があればチェックする
        if race_grade!=5:
            race_grade_name = "check_grade_{}".format(race_grade)
            wf.click_checkbox(driver, race_grade_name)
        # 表示件数を20件にする
        wf.select_from_dropdown(driver, "list", "20")
        # 検索ボタンをクリック
        wf.click_button(driver, "//*[@id='db_search_detail_form']/form/div/input[1]")
        time.sleep(1)

        # 検索結果のレース一覧取得
        raceID_list.extend(get_race_id_list_from_search_result(driver))
        
        # raceID_listが日付降順なので、昇順にする
        # raceID_list.reverse()

        # 検索の開始年月を (ptr + 1) 月からに再設定
        head = ptr + relativedelta(months = 1)

        logger.debug("race_id_list({0}) = {1}".format(len(raceID_list), raceID_list))

    return ("scraping", raceID_list, scrape_race_result, {"lan":False}), # ("scraping", raceID_list, html_save, {}),

path_html = path_ini("common", "path_html")
def html_save(d):
    driver = d["driver"]
    html        = driver.page_source.encode('utf-8')
    current_url = driver.current_url.encode('utf-8')

    # logger.debug(f"html = {html}")
    # logger.debug(f"current_url = {current_url}")

    # 12桁ならrace_id, 10桁ならhorse_id
    id = re.search('[0-9a-zA-Z]{10,12}', current_url).group()
    logger.debug(f"id = {id}")

    if len(id) == 10:
        os.makedirs(path_html + "horse_id/", exist_ok=True)

        p = path_html + "horse_id/" + id + ".html"
        logger.info("save html {0}".format(p))
        with open(p, 'w', encoding='utf-8') as f:
            f.write(html)

    elif len(id) == 12:
        os.makedirs(path_html + "race_id/", exist_ok=True)

        p = path_html + "race_id/" + id + ".html"
        logger.info("save html {0}".format(p))
        with open(p, 'w', encoding='utf-8') as f:
            f.write(html)

    else:
        logger.critical("Cannt parse URL:{0}".format(current_url))

    return ("html", ),



def build_perform_contents(d):
    """ 競走成績テーブルの取得 
    取得に失敗した場合はNoneを返す"""

    driver = d["driver"]
    horse_id = re.search('[0-9a-zA-Z]{10}', driver.current_url).group()

    logger.debug('get result table')

    try:
        element_table = driver.find_element(By.XPATH, "//*[@class='db_h_race_results nk_tb_common']")
    except selenium.common.exceptions.NoSuchElementException:
        return None
    
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

    dfs[0]["horse_id"] = horse_id
    dfs[0]["race_id"] = race_link_list
    dfs[0]["jockey_id"] = jockey_link_list
    dfs[0]["grade"] = grade_list

    return ("db", dfs[0], "race_info"),

def scrape_horse_prof(d):
    """馬のデータを取得して保存する
    driver: webdriver
    horseID: 調べるhorseID
    """

    driver = d["driver"]
    ## 以下保留事項
    # 外国から参加してきた馬はどう処理するのか

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
    # logger.debug('get result table')
    # horse_id = re.search('[0-9a-zA-Z]{10}', driver.current_url).group()
    # race_info = build_perform_contents(driver, horse_id)

    ## 競走成績のデータ取得が成功したかどうかを、通算成績の出走数と競走成績の行数で判定
    # if (race_info is not None) and (num_entry_race == len(race_info)):
    #     check = "1" # OK
    # else:
    #     check = "0" # データ欠損アリ (prof_tableとperform_tableで一致しない)

    prof["blood_f" ] = blood_list[0]
    prof["blood_ff"] = blood_list[1]
    prof["blood_fm"] = blood_list[2]
    prof["blood_m" ] = blood_list[3]
    prof["blood_mf"] = blood_list[4]
    prof["blood_mm"] = blood_list[5]

    prof["horse_id"] = re.search('[0-9a-zA-Z]{10}', driver.current_url).group()
    prof["horse_title"] = horse_title
    prof["check_flg"] = "1" # 固定

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
        
    return ("db", prof, "horse_prof"),
