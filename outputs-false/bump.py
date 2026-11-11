import sys
from pathlib import Path
# py outputs-false/bump.py [number of outputs] [space between outputs] [initial value]
def bump():
    print("creating outputs-false/bump_"+str(sys.argv[1])+"_"+str(sys.argv[2])+".py")
    output_folder = Path("outputs-false")
    x= "bump_"+str(sys.argv[1])+"_"+str(sys.argv[2])+".txt"
    file = output_folder / x
    count = 0
    with open(file, "w", encoding="utf-8") as f:
        w = str(count)+" " +str(sys.argv[3])+ "\n"
        f.write(w)
        count = count + int(sys.argv[2])
        while count <= int(sys.argv[1]) * int(sys.argv[2]):
            w = str(count)+" " +"0"+ "\n"
            f.write(w)
            count = count + int(sys.argv[2])

bump()