import sys
from pathlib import Path
# py outputs-false/flatline.py [number of outputs] [space between outputs] [value]
def flatline():
    print("creating outputs-false/flatline_"+str(sys.argv[1])+"_"+str(sys.argv[2])+".txt")
    output_folder = Path("outputs-false")
    x= "flatline_"+str(sys.argv[1])+"_"+str(sys.argv[2])+".txt"
    file = output_folder / x
    count = 0
    with open(file, "w", encoding="utf-8") as f:
        while count <= int(sys.argv[1]) * int(sys.argv[2]):
            w = str(count)+" " +str(sys.argv[3])+ "\n"
            f.write(w)
            count = count + int(sys.argv[2])

flatline()