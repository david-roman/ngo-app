import json

# Returns general and its specific activity areas from NGOs json.

file = open("./python/esango.json")

dicts = json.loads(file.read())

areas = set([])

# Get general areas
for elem in dicts:
    act = elem.get("activities")
    for a in act:
        areas.add(a)

specific = []

# array of sets, one per general area
for ar in areas:
    specific.append(set([]))

array = list(areas)

# 
for elem in dicts:
    act = elem.get("activities")
    for a in act:
        for val in act[a]:
            index = array.index(a)
            specific[index].add(val)

print(array, [list(x) for x in specific])