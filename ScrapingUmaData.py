from matplotlib.pyplot import get
from selenium import webdriver
import time

# ChromeDriverのパス
DRIVERPATH = "E:\\Git_share\\uma_deep\\HorseRacingAI"

def get_source(driver, url, year, grade):
    driver.get(url)



if __name__ == "__main__":
    driver = webdriver.Chrome(DRIVERPATH + "\\chromedriver")
    URL_find_race_id = "https://db.netkeiba.com/?pid=race_search_detail"
    get_source(driver, URL_find_race_id, 1986, "G1" )