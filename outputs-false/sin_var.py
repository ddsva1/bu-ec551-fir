import sys
from pathlib import Path
import math
import random
# py outputs-false/sin_var.py [number of outputs] [space between outputs] [variance]
def sin_var():
    print("creating outputs-false/sin_var_"+str(sys.argv[1])+"_"+str(sys.argv[2])+"_"+str(sys.argv[3])+".txt")
    output_folder = Path("outputs-false")
    x= "sin_var_"+str(sys.argv[1])+"_"+str(sys.argv[2])+"_"+str(sys.argv[3])+".txt"
    file = output_folder / x
    count = 0
    with open(file, "w", encoding="utf-8") as f:
        while count <= int(sys.argv[1]) * int(sys.argv[2]):
            w = str(count)+" " +str(round(math.sin(math.radians(count+random.randint(-1*int(sys.argv[3]), int(sys.argv[3])))),5))+ "\n"
            f.write(w)
            count = count + int(sys.argv[2])

sin_var()