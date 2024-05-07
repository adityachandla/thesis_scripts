import re

pattern = re.compile(r"([0-9\.]+)\+([0-9\.]+)\+([0-9\.]+)")
heaps = re.compile(r"(\d+)\->(\d+)\->(\d+) MB")

with open("gc.log") as gc:
    lines = gc.read().strip().split('\n')

stw = 0
max_stw = 0
collected = 0
for line in lines:
    matches = pattern.findall(line)[0]
    stw += float(matches[0])
    stw += float(matches[2])
    max_stw = max(max_stw, float(matches[0]), float(matches[2]))

    sizes = heaps.findall(line)[0]
    collected += int(sizes[1])-int(sizes[0])
print(stw)
print(max_stw)
print(collected)
