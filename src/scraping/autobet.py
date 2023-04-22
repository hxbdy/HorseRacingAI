import time

import webdriver_functions as wf
import RaceInfo

from file_path_mgr       import private_ini
from deepLearning_common import read_RaceInfo

class AutoBet:
    def __init__(self) -> None:
        # open()でdriverを初期化してください
        self.driver    = None

        self.browser   = private_ini("scraping", "browser")
        
        self.inet_id   = private_ini("jra", "INET_ID")
        self.member_id = private_ini("jra", "MEMBER_ID")
        self.p_ars_id  = private_ini("jra", "P_ARS_ID")
        self.password  = private_ini("jra", "PASS")

    def _init_driver(self):
        self.driver = wf.start_driver(self.browser, [], False)

    def _final_driver(self):
        self.driver.quit()

    def _inet_login(self):
        wf.access_page(self.driver, "https://www.ipat.jra.go.jp/")
        wf.input_text(self.driver, '//*[@id="top"]/div[3]/div/table/tbody/tr/td[2]/div/div/form/table[1]/tbody/tr/td[2]/span/input', self.inet_id)
        wf.click_button(self.driver, "//*[@id='top']/div[3]/div/table/tbody/tr/td[2]/div/div/form/table[1]/tbody/tr/td[3]/p/a")

    def _member_login(self):
        wf.input_text(self.driver, '//*[@id="main_area"]/div/div[1]/table/tbody/tr[1]/td[2]/span/input', self.member_id)
        wf.input_text(self.driver, '//*[@id="main_area"]/div/div[1]/table/tbody/tr[2]/td[2]/span/input', self.password)
        wf.input_text(self.driver, '//*[@id="main_area"]/div/div[1]/table/tbody/tr[3]/td[2]/span/input', self.p_ars_id)
        wf.click_button(self.driver, '//*[@id="main_area"]/div/div[1]/table/tbody/tr[1]/td[3]/p/a')

    # venue
    def _click_tokyo_sat(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[2]/div[1]/div[1]/button')
    def _click_tokyo_sun(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[2]/div[2]/div[1]/button')
    def _click_kyoto_sat(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[2]/div[1]/div[2]/button')
    def _click_kyoto_sun(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[2]/div[2]/div[2]/button')
    def _click_fukushima_sat(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[2]/div[1]/div[3]/button')

    # RaceNo
    def _click_1R(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[4]/div[1]/button')
    def _click_2R(self):
         wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[4]/div[2]/button')
    def _click_3R(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[4]/div[3]/button')
    def _click_4R(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[4]/div[4]/button')
    def _click_5R(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[4]/div[5]/button')
    def _click_6R(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[4]/div[6]/button')
    def _click_7R(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[4]/div[7]/button')
    def _click_8R(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[4]/div[8]/button')
    def _click_9R(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[4]/div[9]/button')
    def _click_10R(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[4]/div[10]/button')
    def _click_11R(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[4]/div[11]/button')
    def _click_12R(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/select-course-race/div/div[2]/div[2]/div[4]/div[12]/button')

    def _getvenue(self, venue):
        d = {
            "東京(土)" : self._click_tokyo_sat,
            "東京(日)" : self._click_tokyo_sun,
            "京都(土)" : self._click_kyoto_sat,
            "京都(日)" : self._click_kyoto_sun,
            "福島(土)" : self._click_fukushima_sat
        }
        return d[venue]

    def _getRaceNo(self, race_no):
        d = {
            "1R" : self._click_1R,
            "2R" : self._click_2R,
            "3R" : self._click_3R,
            "4R" : self._click_4R,
            "5R" : self._click_5R,
            "6R" : self._click_6R,
            "7R" : self._click_7R,
            "8R" : self._click_8R,
            "9R" : self._click_9R,
            "10R" : self._click_10R,
            "11R" : self._click_11R,
            "12R" : self._click_12R
        }
        return d[race_no]

    def _normal_bet(self):
        time.sleep(1)
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/main/div[2]/div[1]/div[1]/button')

    def _select_type(self, type):
        time.sleep(1)
        wf.select_from_id_dropdown(self.driver, "bet-basic-type", type)

    def _select_method(self, method):
        time.sleep(1)
        wf.select_from_id_dropdown(self.driver, "bet-basic-method", method)

    def _select_horse_no(self, no_list):
        for no in no_list:
            n = "no" + str(no)
            wf.click_js_checkbox(self.driver, n)

    def _bet_money(self, money):
        wf.input_text(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/div/div[3]/select-list/div/div/div[3]/div[1]/input', int(money / 100))

    def _expand_set(self):
        wf.click_button(self.driver, '//*[@id="main"]/ui-view/div[2]/ui-view/main/div/div[3]/select-list/div/div/div[3]/div[4]/button[1]')

    def _vote(self):
        time.sleep(1)
        wf.click_button(self.driver, '//*[@id="ipat-navbar"]/div/ng-transclude/div/ul/li/button')
        time.sleep(1)
        money = wf.get_class_text(self.driver, '//*[@id="bet-list-top"]/div[5]/table/tbody/tr[5]/td/span[2]')
        wf.input_text(self.driver, '//*[@id="bet-list-top"]/div[5]/table/tbody/tr[6]/td/input', money)

    def _buy(self):
        wf.click_button(self.driver, '//*[@id="bet-list-top"]/div[5]/table/tbody/tr[7]/td/button')
        time.sleep(1)
        wf.click_button(self.driver, '/html/body/error-window/div/div/div[3]/button[1]')

    ####################################################################

    def bet(self, venue, race_no, type, method, horse_no, money):
        # driver init
        self._init_driver()
        
        # login
        self._inet_login()
        self._member_login()

        # 通常投票
        self._normal_bet()

        time.sleep(1)
        self._getvenue(venue)()
        self._getRaceNo(race_no)()
        self._select_type(type)
        self._select_method(method)

        # check
        self._select_horse_no(horse_no)

        # bet
        self._bet_money(money)

        # set
        self._expand_set()

        # confirm
        self._vote()

        confirm = input("BET? PRESS Y/[N] : ")

        if confirm.lower() == "y":
            self._buy()
        else:
            print("bet cancel")

        # driver finalize
        input("input any key to exit...")
        self._final_driver()


############################################################################
if __name__ == "__main__":
    better = AutoBet()

    # レース情報読み込み
    tmp_param:RaceInfo = read_RaceInfo()

    # ベット内容確認
    bet1, bet2, bet3 = tmp_param.predict_y[0:3]

    better.bet(venue=tmp_param.venue, race_no=tmp_param.race_no, type="ワイド", method="ボックス", horse_no=[bet1 + 1, bet2 + 1, bet3 + 1], money=100)
