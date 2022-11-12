# 複数プロセスから同じログファイルへの書き込みを行う
# 参考 :
# 超簡単Pythonで複数（マルチ）プロセスから単一ログファイル出力処理｜10mohi6｜note
# https://note.com/10mohi6/n/n9ccf4468fa4f
# > python ./src/sample/sample_multiproc_log2.py

import logging
import logging.handlers
import multiprocessing as mp

def listener(q):
    # ロガーセットアップ
    logger = logging.getLogger()
    h = logging.handlers.TimedRotatingFileHandler("mp.log", when="midnight", backupCount=20)
    f = logging.Formatter("%(asctime)s %(processName)-10s %(name)-10s %(levelname)-8s %(message)s")
    h.setFormatter(f)
    logger.addHandler(h)
    
    # リスナー部分
    while True:
        logger.handle(q.get())

class Parent:
    def worker_configurer(self, q):
       h = logging.handlers.QueueHandler(q)
       root = logging.getLogger()
       root.addHandler(h)
       root.setLevel(logging.DEBUG)

class Child(Parent):
    def worker(self, q):
       self.worker_configurer(q)
       logger = logging.getLogger()
       for i in range(3):
           logger.info("message #{}".format(i))



if __name__ == '__main__':
    q = mp.Queue()

    pl = mp.Process(name="listener", target=listener, args=(q,),)

    child1 = Child()
    child2 = Child()

    # 各プロセスにキューを渡す必要あり
    pw1 = mp.Process(name="worker1", target=child1.worker, args=(q,),)
    pw2 = mp.Process(name="worker2", target=child2.worker, args=(q,),)


    pl.start()
    pw1.start()
    pw2.start()
    pw1.join()
    pw2.join()
    pl.join()
