from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

import time

# ChromeDriverのパス
DRIVERPATH = "E:\\Git_share\\uma_deep\\HorseRacingAI"

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


"""主要部"""
def get_raceID(driver, yearlist, race_class_list=["check_grade_1"]):
    """
    検索をかけてraceIDを取得する。
    yearlist: 取得する年のリスト(1986-2022)
    race_class_list: 取得するクラスのリスト(G1, G2, opなど) 1: G1, 2: G2, 3: G3, 4: OP
    """

    raceIDs_all = []
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

            raceIDs_all += raceIDs_year

    return raceIDs_all

def get_horseID_racedata(driver, raceID_list):
    """
    horseIDを取得する & race情報を得る。
    raceID_list: 調べるraceIDのリスト
    """
    horseIDs_all = set()
    race_data_all = []
    
    for raceID in raceID_list:
        ## レースページにアクセス
        race_url = "https://db.netkeiba.com/race/{}/".format(raceID)
        go_page(driver, race_url)

        ## horseIDの取得とhorseIDs_allへの保存
        horse_column_html = driver.find_elements(By.XPATH, "//*[@class='race_table_01 nk_tb_common']/tbody/tr/td[4]")
        horseIDs_race = []
        for i in range(len(horse_column_html)):
            horse_url_str = horse_column_html[i].find_element(By.TAG_NAME,"a").get_attribute("href")
            horseID = horse_url_str[horse_url_str.find("horse/")+6 : -1] # 最後の/を除去
            horseIDs_race.append(horseID)
        horseIDs_all |= set(horseIDs_race)


        ## race情報の取得 (払い戻しの情報は含まず)
        # レース名, レースデータ1(天候など), レースデータ2(日付など)  <未補正 文字列>
        race_name = driver.find_element(By.XPATH,"//*[@id='main']/div/div/div/diary_snap/div/div/dl/dd/h1").text
        race_data1 = driver.find_element(By.XPATH,"//*[@id='main']/div/div/div/diary_snap/div/div/dl/dd/p/diary_snap_cut/span").text
        race_data2 = driver.find_element(By.XPATH,"//*[@id='main']/div/div/div/diary_snap/div/div/p").text
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
        
        race_data = [race_name, race_data1, race_data2, horseIDs_race, goal_time, goal_dif, horse_weight, money]
        race_data_all.append(race_data)

    
    return list(horseIDs_all), race_data_all



if __name__ == "__main__":
    # Chromeを起動 (エラーメッセージを表示しない)
    ChromeOptions = webdriver.ChromeOptions()
    ChromeOptions.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(DRIVERPATH + "\\chromedriver", options=ChromeOptions)
    
    # raceIDを取得してくる
    race_class_list =["check_grade_1", "check_grade_2", "check_grade_3"]
    raceIDs_all = get_raceID(driver, list(range(1986,1987)), race_class_list)
    
    # horseIDを取得する & race情報を得る
    #raceIDs_all = ["198606050810"] #test用
    horse_IDs_all, race_data_all = get_horseID_racedata(driver, raceIDs_all)

    # 馬データを取得してくる
    #horseID_list = ["1983104089"] #test用
    horseID_list = horse_IDs_all
    horse_data_all = []
    for horseID in horseID_list:
        ## 馬のページにアクセス
        horse_url = "https://db.netkeiba.com/horse/{}/".format(horseID)
        go_page(driver, horse_url)

        ## プロフィールテーブルの取得
        prof_table = driver.find_element(By.XPATH, "//*[@class='db_prof_table no_OwnerUnit']/tbody")
        ## 血統テーブルの取得
        blood_table = driver.find_element(By.XPATH, "//*[@class='blood_table']/tbody")
        ## 競走成績テーブルの取得
        perform_table = driver.find_element(By.XPATH, "//*[@class='db_h_race_results nk_tb_common']/tbody")

        horse_data = [horseID, prof_table, blood_table, perform_table]
        horse_data_all.append(horse_data)

        ## がんばって整形する

        ## 以下保留事項
        # 血統を評価する際に、horseIDs_allから辿れない馬(収集期間内にG1,G2,G3に出場経験のない馬)のhorseIDをどこかに保存しておく
        # 血統テーブルから過去の馬に遡ることになるが、その過去の馬のデータが無い場合どうするか
        # そもそも外国から参加してきた馬はどう処理するのか
    