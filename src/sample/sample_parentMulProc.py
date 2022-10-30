# マルチプロセス間で共通の親がいて、親の変数を変えたとき、もう一方でも値は変わるのか。
# python ./src/sample/sample_parentMulProc.py

# 確認結果 -> 
# 親クラスの値の書き換え処理を子クラスA,Bそれぞれで行ってもそれぞれに影響しない
# val = 0
# inc val 1
# val = 0
# inc val 2
# val = 0
# inc val 3
# val = 0
# inc val 4
# val = 0
# inc val 5
# val = 0
# inc val 6
# val = 0
# inc val 7
# val = 0
# inc val 8
# val = 0
# inc val 9

from multiprocessing import Process
import time

class Parent:
    val = 0

    def __init__(self) -> None:
        pass

class Child_1(Parent):
    def __init__(self) -> None:
        pass

    def loop(self):
        while True:
            print("val = {0}".format(Parent.val))
            time.sleep(1)

class Child_2(Parent):
    def __init__(self) -> None:
        pass

    def inc(self):
        while True:
            Parent.val += 1
            print("inc val = {0}".format(Parent.val))
            time.sleep(1)


if __name__ == "__main__":
    child_1 = Child_1()
    child_2 = Child_2()

    process_1 = Process(target = child_1.loop)
    process_1.start()

    process_2 = Process(target = child_2.inc)
    process_2.start()
