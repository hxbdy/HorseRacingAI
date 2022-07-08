import cupy as cp
import numpy as np
import time

A_cpu = np.random.randn(5000, 10000)
B_cpu = np.random.randn(10000, 15000)

# numpy を使ってCPUで行列積を計算する
print ("Calc dot with cpu...")
start = time.time()
AB_cpu = np.dot(A_cpu, B_cpu)
elapsed_time = time.time() - start
print ("CPU elapsed_time:{0}".format(elapsed_time) + "[sec]")

# np.ndarray から GPU 上のメモリにデータを移動する
A_gpu = cp.asarray(A_cpu)
B_gpu = cp.asarray(B_cpu)

# cupy を使って GPU で行列積を計算する
print ("Calc dot with gpu...")
start = time.time()
AB_gpu = cp.dot(A_gpu, B_gpu)
elapsed_time = time.time() - start
print ("GPU elapsed_time:{0}".format(elapsed_time) + "[sec]")

# メインメモリ上にデータを移動する
AB_cpu2 = AB_gpu.get()  # AB_cpu2 は np.ndarray 型
