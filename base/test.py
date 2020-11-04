a = {1:1,2:2,3:3,4:4}
b = []
for k,v in a.items():
    if k <=2:
        b.append(k)
print(b)
for i,val in enumerate(b):
    del a[val]
print(a)