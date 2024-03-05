import json
import os

path1 = "output2/negative_samples.json"
path2 = "output4"
with open(path1, "r") as f:
    data = json.load(f)

if not os.path.exists(path2):
    os.makedirs(path2)

index = 0

with open(os.path.join(path2, "product_old.java"), "w") as f:
    f.write(data[index]["product_old_content"])

with open(os.path.join(path2, "product_new.java"), "w") as f:
    f.write(data[index]["product_new_content"])

with open(os.path.join(path2, "test_old.java"), "w") as f:
    f.write(data[index]["test_old_content"])

with open(os.path.join(path2, "test_new.java"), "w") as f:
    f.write(data[index]["test_new_content"])