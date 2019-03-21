from collections import defaultdict

testDict = defaultdict(list)

keys = ['a',
        'b',
        'c',
        'd',
        'e',
        'f',
        'g',
        'h',
        'i',
        'j',
        'k',
        'l',
        'm',]

vals = [x for x in range(1, 16)]

for x in range(0, 7):
    for y in vals:
        testDict[keys[x]].append(y)

print(testDict)