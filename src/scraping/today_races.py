# 今日開催されるレース一覧を取得し
# 各レース30分前にpredict.batを実行する

import time
import datetime
import re
import subprocess

import schedule
from rich.console import Console
from selenium.webdriver.common.by import By

import webdriver_functions as wf
from file_path_mgr import private_ini

class TodayRaces:
    def __init__(self) -> None:
        # open()でdriverを初期化してください
        self.driver    = None

        self.browser   = private_ini("scraping", "browser")

    def _init_driver(self):
        self.driver = wf.start_driver(self.browser, [], False)

    def _final_driver(self):
        self.driver.quit()

    def _get_race_id_list(self, elements):
        race_id_list = []
        for element in elements:
            race_ids = element.find_elements(By.TAG_NAME, "a")
            for url in race_ids:
                race_id = url.get_attribute("href")
                race_id = re.findall("\d{12}", race_id)[0]

                if not (race_id in race_id_list):
                    race_id_list.append(race_id)

        return race_id_list
    
    def _get_race_time_list(self, elements):
        race_time_list = []
        for element in elements:
            race_times = element.find_elements(By.CLASS_NAME, "RaceList_Itemtime")
            for race_time in race_times:
                start_time = race_time.text

                if not (start_time in race_time_list):
                    race_time_list.append(start_time)

        return race_time_list
    
    def _access_time_table(self):
        today = datetime.datetime.now().strftime("%Y%m%d")
        wf.access_page(self.driver, "https://race.netkeiba.com/top/race_list.html?kaisai_date=" + today)

    def _bet_time(self, race_time_list):
        bet_time_list = []
        for race_time in race_time_list:
            bet_time = datetime.datetime.strptime(race_time, '%H:%M') - datetime.timedelta(minutes=30)
            bet_time = bet_time.strftime('%H:%M')
            bet_time_list.append(bet_time)
        return bet_time_list

    def _get_time_table(self):
        elements = self.driver.find_elements(By.CLASS_NAME, "RaceList_Data")
        race_id_list   = self._get_race_id_list(elements)
        race_time_list = self._get_race_time_list(elements)

        bet_time_list = self._bet_time(race_time_list)
        race_time_dict = dict(zip(race_id_list, bet_time_list))
        return race_time_dict
    
    def _sort_dict_value(self, dic):
        return dict(sorted(dic.items(), key = lambda dic : dic[1]))

    def get(self):
        self._init_driver()

        self._access_time_table()
        race_time_dict = self._get_time_table()

        # 出走時間でソート
        race_time_dict = self._sort_dict_value(race_time_dict)
        print(race_time_dict)

        self._final_driver()

        return race_time_dict


############################################################################

def bat_exe(race_id):
    cmd = ['predict.bat', '--race_id', race_id, '--skip_login']
    proc = subprocess.Popen(cmd, encoding='shift-jis', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:
        
        line = proc.stdout.readline()
        if line:
            print(line, end='')

        if not line and proc.poll() is not None:
            break

    return schedule.CancelJob

if __name__ == "__main__":
    
    today = TodayRaces()
    race_time_dict = today.get()

    # debug用
    # race_time_dict = {"202305020201":"23:40"}

    for race_id in race_time_dict.keys():
        print(race_id, race_time_dict[race_id])
        schedule.every().day.at(race_time_dict[race_id]).do(bat_exe, race_id=race_id)

    console = Console()
    with console.status("[bold green]Waiting for next bet ...") as status:
        while True:
            n = schedule.idle_seconds()
            if n is None:
                break
            elif n > 0:
                jobs = schedule.get_jobs()
                status.update("[bold green]Waiting for next bet -> " + jobs[0].next_run.strftime('%H:%M'))
                time.sleep(n)
            schedule.run_pending()
        console.log(f'[bold][red]Done')
