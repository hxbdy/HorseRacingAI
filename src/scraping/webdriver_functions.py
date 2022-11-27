# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

import time
import logging

from debug import stream_hdl, file_hdl

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#loggerにハンドラを設定
logger.addHandler(stream_hdl(logging.INFO))
logger.addHandler(file_hdl("output"))

# webdriver を保存するディレクトリ
DRIVER_DIRECTORY = 'src\\scraping'


def start_driver(browser_name):
    """ブラウザの起動
    browser_name: 使用ブラウザ(Chrome or FireFox)
    ドライバが存在しない場合は自動でインストールする．
    """
    if(browser_name == 'Chrome'):
        # Chromeを起動 (エラーメッセージを表示しない)
        logger.info('initialize chrome driver')
        service = Service(executable_path=ChromeDriverManager(path=DRIVER_DIRECTORY).install())
        ChromeOptions = webdriver.ChromeOptions()
        ChromeOptions.add_experimental_option("excludeSwitches", ["enable-logging"])
        ChromeOptions.add_argument('-incognito') # シークレットモード
        # ChromeOptions.add_argument('--headless') # ヘッドレスモード
        driver = webdriver.Chrome(service=service, options=ChromeOptions)
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

def click_checkbox(driver, checkbox_id):
    """チェックボックスをクリックする
    """
    driver.find_element(By.ID, str(checkbox_id)).click()

def click_button(driver, xpath):
    """ボタンをクリックする
    """
    driver.find_element(By.XPATH, xpath).click()
