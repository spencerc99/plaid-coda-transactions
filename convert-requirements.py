f = open(r"requirements.txt", "r").read()
f1 = f.split("\n")
for line in f1:  
    if "=" in line:
       a = line.split("=")[0:-1]
       print(a[0]+"==" + a[1])
