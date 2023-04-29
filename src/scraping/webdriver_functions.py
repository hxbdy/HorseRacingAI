# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import time

from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# webdriver を保存するディレクトリ
DRIVER_DIRECTORY = 'src\\scraping'


def start_driver(browser_name, arg_list=[], pageLoadStrategy=False):
    """ブラウザの起動
    browser_name: 使用ブラウザ(Chrome or FireFox)
    arg_list: ブラウザ起動オプション(Chrome限定)
    pageLoadStrategy: ページの読み込みを待機するか(Chrome限定)True: 待たない。False:待つ
    ドライバが存在しない場合は自動でインストールする．
    """
    if(browser_name == 'Chrome'):
        # Chromeを起動 (エラーメッセージを表示しない)
        logger.info('initialize chrome driver')
        service = Service(executable_path=ChromeDriverManager(path=DRIVER_DIRECTORY).install())
        ChromeOptions = webdriver.ChromeOptions()

        # 起動オプション追加
        # ChromeOptions.add_argument('-incognito')                           # シークレットモード
        # ChromeOptions.add_argument('--headless')                           # ヘッドレスモード
        # ChromeOptions.add_argument('--disable-logging')                    # ログ無効
        # ChromeOptions.add_argument('--user-agent=hogehoge')                # UA設定
        # ChromeOptions.add_argument('--blink-settings=imagesEnabled=false') # 画像を取得しない
        for arg in arg_list:
            ChromeOptions.add_argument(arg)

        # HIDエラー回避
        ChromeOptions.add_experimental_option("excludeSwitches", ["enable-logging"])

        # ページの読み込みを待たない
        if pageLoadStrategy:
            desired = DesiredCapabilities().CHROME
            desired['pageLoadStrategy'] = 'none'
        else:
            desired = None

        driver = webdriver.Chrome(service=service, options=ChromeOptions, desired_capabilities=desired)
        logger.info('initialize chrome driver completed')
    
    elif(browser_name == 'FireFox'):
        # Firefoxを起動
        logger.info('initialize firefox driver')
        service = Service(executable_path=GeckoDriverManager(path=DRIVER_DIRECTORY).install())
        driver = webdriver.Firefox(service=service)
        logger.info('initialize firefox driver completed')

    return driver

def access_page(driver, url):
    """url先にアクセスする
    """
    logger.debug('accessing {}'.format(url))
    driver.get(url)
    time.sleep(1)

def select_from_dropdown(driver, select_name, select_value):
    """ドロップダウンから値を選択する
    """
    select = Select(driver.find_element(By.NAME, str(select_name)))
    select.select_by_value(str(select_value))

def select_from_id_dropdown(driver, id, select_value):
    """ドロップダウン から値を適用する(id使用)
    """
    select = Select(driver.find_element(By.ID, id))
    select.select_by_visible_text(str(select_value))

def click_checkbox(driver, checkbox_id):
    """チェックボックスをクリックする
    """
    driver.find_element(By.ID, str(checkbox_id)).click()

def click_js_checkbox(driver, checkbox_id):
    """チェックボックスをjsでクリックする
    """
    element = driver.find_element(By.ID, str(checkbox_id))
    driver.execute_script('arguments[0].click();', element)

def click_button(driver, xpath):
    """ボタンをクリックする
    """
    driver.find_element(By.XPATH, xpath).click()

def input_text(driver, xpath, text):
    """テキストボックスに入力する
    """
    driver.find_element(By.XPATH, xpath).send_keys(text)

def get_class_text(driver, xpath):
    """タグの中から文字列を取得する
    """
    return driver.find_element(By.XPATH, xpath).text
