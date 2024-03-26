import json
import difflib
import os
import find_commit_hash_in_range

project_name = "jfreechart"

# 路径可能需要根据你的json文件位置进行修改
json_file_path = f'{project_name}_output/filter.json'

# java -jar gumtree.jar textdiff temp/temp_old.java temp/temp_new.java -f JSON -o temp/temp.json


# 读取JSON文件
with open(json_file_path, 'r') as file:
    data = json.load(file)

index_negative = 0
index_positive = 0
null_number = 0
project_path = f"/home/yeren/java-project/{project_name}"
output_dir = f"/home/yeren/TestEvolution/{project_name}_output"
currrent_path = os.getcwd()

# 创建文件夹
os.makedirs(os.path.join(output_dir, 'positive_output'), exist_ok=True)
os.makedirs(os.path.join(output_dir, 'negative_output'), exist_ok=True)

# 处理每个元素
for index, item in enumerate(data):
    tag = item['tag']
    product_commit = item['product_commit']
    test_commit = item['test_commit']
    os.chdir(project_path)
    product_time = find_commit_hash_in_range.get_commit_date(product_commit)
    test_time = find_commit_hash_in_range.get_commit_date(test_commit)
    os.chdir(currrent_path)
    date_format = "%Y-%m-%d_%H:%M"
    product_time_str = product_time.strftime(date_format)
    test_time_str = test_time.strftime(date_format)
    product_path = item['product_file_path']
    test_path = item['test_file_path']
    try:
        product_old_content = item['product_old_content'].splitlines()
        product_new_content = item['product_new_content'].splitlines()
        test_old_content = item['test_old_content'].splitlines()
        test_new_content = item['test_new_content'].splitlines()
    except:
        null_number += 1
        # print(f"null content in tag {tag}")
        continue

    # 生成差异
    product_diff = list(difflib.unified_diff(product_old_content, product_new_content, lineterm=''))
    test_diff = list(difflib.unified_diff(test_old_content, test_new_content, lineterm=''))

    # 保存差异文件
    product_path_handle = '_'.join(product_path[:-5].split('/'))
    test_path_handle = '_'.join(test_path[:-5].split('/'))
    if tag == 'positive':
        output_folder = os.path.join(output_dir, 'positive_output') 
        index_positive += 1 
        with open(f'{output_folder}/{index_positive}_product_{product_time_str}.diff', 'w') as file:
            file.write(f'{product_commit}\n{product_path}\n' + '\n'.join(product_diff))
        with open(f'{output_folder}/{index_positive}_test_{test_time_str}.diff', 'w') as file:
            file.write(f'{test_commit}\n{test_path}\n' + '\n'.join(test_diff))
    else:
        output_folder = os.path.join(output_dir, 'negative_output')
        index_negative += 1
        with open(f'{output_folder}/{index_negative}_product_{product_time_str}.diff', 'w') as file:
            file.write(f'{product_commit}\n{product_path}\n' + '\n'.join(product_diff))
        with open(f'{output_folder}/{index_negative}_test_{test_time_str}.diff', 'w') as file:
            file.write(f'{test_commit}\n{test_path}\n' + '\n'.join(test_diff))


print(f"positive number: {index_positive}")
print(f"negative number: {index_negative}")
print(f"number of null content: {null_number}")