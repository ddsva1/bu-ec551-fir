import sys
from pathlib import Path
import math
# py outputs-false/sin.py [number of outputs] [space between outputs]
def sin():
    print("creating outputs-false/sin_"+str(sys.argv[1])+"_"+str(sys.argv[2])+".txt")
    output_folder = Path("outputs-false")
    x= "sin_"+str(sys.argv[1])+"_"+str(sys.argv[2])+".txt"
    file = output_folder / x
    count = 0
    with open(file, "w", encoding="utf-8") as f:
        while count <= int(sys.argv[1]) * int(sys.argv[2]):
            w = str(count)+" " +str(round(math.sin(math.radians(count)),5))+ "\n"
            f.write(w)
            count = count + int(sys.argv[2])

sin()