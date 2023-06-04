from log import *
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

import re
import os
import time
import argparse
import datetime
import glob
from pathlib import Path
import queue
from dateutil.relativedelta import relativedelta
from multiprocessing        import Process, Queue
from collections            import deque

import selenium
from selenium.webdriver.common.by import By
import pandas as pd
import numpy as np
import psutil

import webdriver_functions as wf
import scraping_functions  as sf

from NetkeibaDB_IF import NetkeibaDB_IF
from file_path_mgr import path_ini, private_ini

from deepLearning_common import write_RaceInfo
from RaceInfo      import RaceInfo

# 長時間スクレイピングが予想される場合、スクレイピング以外の作業を同じマシン上で行いたい時向け
# スクレイピングプロセスの優先度設定(通常以上にはしないこと)
# 通常以下 : psutil.BELOW_NORMAL_PRIORITY_CLASS
# 通常     : psutil.NORMAL_PRIORITY_CLASS
psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)

def db_ctrl(db_ctrl_queue):
    logger.debug("db_ctrl start")
    nf = NetkeibaDB_IF("ROM", read_only=False)
    while True:
        try:
            logger.info("db_ctrl queue remain: {0}".format(db_ctrl_queue.qsize()))
            df, df_name = db_ctrl_queue.get(timeout=300)
            logger.debug("db_ctrl rcv")
            nf.db_insert_pandas(df, df_name)
        except queue.Empty:
            logger.info("db_ctrl process exception ! break...")
            break

def scrape(scraping_queue, db_ctrl_queue):
    logger.debug("scrape start")
    arg_list = ['--disable-logging', '--blink-settings=imagesEnabled=false']
    browser = private_ini("scraping", "browser")
    driver = wf.start_driver(browser, arg_list, False)

    while True:
        try:
            logger.info("scrape queue remain: {0}".format(scraping_queue.qsize()))
            url, func, arg_dict = scraping_queue.get(timeout=180)
            wf.access_page(driver, url)
        except queue.Empty:
            logger.info("scrape process exception ! break...")
            break

        arg_dict["driver"] = driver
        rets = func(arg_dict)

        logger.debug("rets = {0}".format(rets))

        for ret in rets:
            if ret[0] == "db":
                logger.debug("cat:db  PUT -> db_ctrl_queue")
                df, df_name = ret[1:]
                db_ctrl_queue.put([df, df_name])
            elif ret[0] == "scraping":
                logger.debug("cat:scraping  PUT -> scraping_queue")
                url, func, arg_dict = ret[1:]
                if type(url) is list:
                    for u in url:
                        scraping_queue.put([u, func, arg_dict])
                else:
                    scraping_queue.put([url, func, arg_dict])
            elif ret[0] == "html":
                logger.debug("cat:html  PUT -> None")
                
    driver.close()

def generator_local_html(path):
    """指定パスにあるファイルの絶対パスをジェネレータで返す"""
    for p in glob.glob(path):
        yield os.path.abspath(p)

if __name__ == "__main__":
    # 済 201904

    scraping_queue = Queue()
    db_ctrl_queue  = Queue()

    proc = [
        Process(target=scrape, args=(scraping_queue, db_ctrl_queue)),
        # Process(target=scrape, args=(scraping_queue, db_ctrl_queue)),
        # Process(target=scrape, args=(scraping_queue, db_ctrl_queue)),
        # Process(target=scrape, args=(scraping_queue, db_ctrl_queue)),
        # Process(target=scrape, args=(scraping_queue, db_ctrl_queue)),
        # Process(target=scrape, args=(scraping_queue, db_ctrl_queue)),
        # Process(target=scrape, args=(scraping_queue, db_ctrl_queue)),
        # Process(target=scrape, args=(scraping_queue, db_ctrl_queue)),
        # Process(target=scrape, args=(scraping_queue, db_ctrl_queue)),
        # Process(target=scrape, args=(scraping_queue, db_ctrl_queue)),
        # Process(target=scrape, args=(scraping_queue, db_ctrl_queue)),

        Process(target=db_ctrl, args=(db_ctrl_queue,)),
    ]

    for p in proc: p.start()

    arg_dict = {
        "start_YYMM" : "201901",
        "end_YYMM"   : "201901",
        "race_grade" : 5
    }
    scraping_queue.put(["https://db.netkeiba.com/?pid=race_search_detail", sf.scrape_raceID, arg_dict])

    # ==========================================
    # htmlを保存する仕組み
    # 保存したあとのhtmlからほしかったデータが抜けなかったため一旦保留中

    # path_html = path_ini("common", "path_html")

    # race_id htmlからrace_resultテーブルの構築
    # path_html_race_id = path_html + "race_id/"

    # with os.scandir(path=path_html_race_id) as it:    
    #     for entry in it:
    #         # LANファイルからdriver生成、DB構築
    #         logger.info(f"html path = {os.path.abspath(entry.path)}")
    #         scraping_queue.put([os.path.abspath(entry.path), sf.scrape_race_result, {"lan":True}])
    #         time.sleep(10)

    # horse_id htmlからrace_info, horse_profテーブルの構築
    # path_html_horse_id = path_html + "horse_id/"

    # targetPath = Path(path_html_horse_id)
    # for item in targetPath.glob('./*'):
    #     # LANファイルからdriver生成、DB構築
    #     logger.info(f"html path = {item.absolute()}")
    #     scraping_queue.put([item.absolute(), sf.scrape_horse_prof, {}])
    #     scraping_queue.put([item.absolute(), sf.build_perform_contents, {}])

    for p in proc: p.join()
