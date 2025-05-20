# %%
from itertools import product
from multiprocessing import Pool, Process, set_start_method
# from concurrent.futures import ProcessPoolExecutor

# set_start_method("spawn")

# %%
things = [1, 2, 3, 4]

def hello():
    print("hello")

if __name__ == "__main__":
    p1 = Process(target=hello)

    p1.start()

    p1.join()

    p1


