import json
import os
import get_modified_files
import find_commit_hash_in_range
import save_git_log_to_file
import parse_git_log
import re
from tqdm import tqdm
import logging
import subprocess
import handle_git_log

logging.basicConfig(filename="debug.log", level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
temp_folder = "temp"
# current_path = "/Users/mac/Desktop/TestEvolution" # mac
current_path = "/home/yeren/TestEvolution" # omen
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

def read_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)
    

def product_code_filter(changed_file_path):
    if "src/main/java" in changed_file_path and changed_file_path.endswith(".java"):
        return True
    return False

def test_product_code_filter(change_file_path, related_product_file_path):
    # test_file_name = change_file_path.split('/')[-1]
    # if 'test' not in test_file_name.lower():
    #     return False
    path_info = re.sub(r"src/main/java", "src/test/java", related_product_file_path)
    if change_file_path == path_info[:-5] + "Test.java":
        return True
    return False

# def gumtree_filter(old_content, new_content):
#     # 筛选新旧文件的修改内容只是注释修改的情况
#     if old_content == None or new_content == None:
#         return False
#     # 获取当前工作路径
#     now_path = os.getcwd()
#     # 切换至对应的项目目录
#     os.chdir(current_path)
#     old_path = os.path.join(temp_folder, "temp_old.java")
#     new_path = os.path.join(temp_folder, "temp_new.java")
#     target_path = os.path.join(temp_folder, "temp_target.json")
#     with open(old_path, "w") as file:
#         file.write(old_content)
#     with open(new_path, "w") as file:
#         file.write(new_content)
#     command = f"java -jar gumtree.jar textdiff {old_path} {new_path} -f JSON -o {target_path}"
#     try:
#         result = subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
#         # return result.stdout.strip()
#     except subprocess.CalledProcessError as e:
#         # print(f"Error running command {' '.join(command)}: {e}")
#         logging.error(f"Error running command {' '.join(command)}: {e}")
#         return False
#     ret = read_json(target_path)
#     actions =  ret["actions"]
#     os.chdir(now_path)
#     if len(actions) == 0:
#         return False
#     for action in actions:
#         change_type = action['tree'].split(":")[0]
#         if change_type != "TextElement":
#             return True
#     return False

def save_PT_pair_low(json_block, output_file_path):
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as file:
            PT_pairs = json.load(file)
    else:
        PT_pairs = []
    PT_pairs.append(json_block)
    with open(output_file_path, 'w') as file:
        json.dump(PT_pairs, file, indent=4)

def save_PT_pair(json_block, output_file_path):
    # 将json_block转换为字符串（一行）
    json_str = json.dumps(json_block)
    # 检查文件是否存在，如果不存在，则先创建文件
    if not os.path.exists(output_file_path):
        with open(output_file_path, 'w') as file:
            pass  # 创建文件，但不写入任何内容
    # 以追加模式打开文件，并写入新的json_block
    with open(output_file_path, 'a') as file:
        file.write(json_str + '\n')  # 追加json字符串并换行


def construct_PT_pair(project_path, output_dir, commit_info_list):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if commit_info_list is None:
        return
        
    # 切换至对应的项目目录
    os.chdir(project_path)
    # 遍历从该项目下获取的每个commit
    positive_total = 0
    negative_total = 0
    for commit_info in tqdm(commit_info_list):
        # print(f"Processing commit {commit_hash}")
        commit_hash = commit_info['commit']
        commit_hash = commit_hash.split(' ')[-1]
        # 获取该commit下的所有修改文件
        changed_files_paths = get_modified_files.get_changed_files(commit_hash)
        # with open("/Users/mac/Desktop/TestEvolution/changed_files.txt", "a") as file:
        #     file.write(commit_hash + "\n")
        #     for changed_files_path in changed_files_paths:
        #         file.write(changed_files_path + "\n")
        #     file.write("\n")
        # print(len(changed_files_paths))
        # 过滤出product code文件
        product_files_paths = list(filter(product_code_filter, changed_files_paths))
        # print(len(product_files_paths))

        if len(product_files_paths) > 0:
            # 获取该commit之后12个小时内的commit
            positive_related_commits = find_commit_hash_in_range.find_commits(commit_hash, 0, 12)
            # 获取该commit之后12小时到480小时内的commit，468=480-12
            negative_related_commits = find_commit_hash_in_range.find_commits(commit_hash, 12, 468)
            # 对于每个product code文件，获取其相关的test code文件，
            # 12h以内全部为正样本，12h到480h为负样本，不考虑product与test文件的对应关系（后续筛选会处理）
            # save_PT_pair({"origin": commit_hash, "positive": positive_related_commits, "negative": negative_related_commits}, "/home/yeren/TestEvolution/commits.json")
            
            if positive_related_commits is not None:
                for positive_related_commit in positive_related_commits:
                    related_changed_files = get_modified_files.get_changed_files(positive_related_commit)
                    for product_files_path in product_files_paths:
                        filter_changed_files = ""
                        for related_changed_file in related_changed_files:
                            if test_product_code_filter(related_changed_file, product_files_path):
                                filter_changed_files = related_changed_file
                                break
                        if filter_changed_files != "":
                            # print("find a positive sample")
                            positive_total += 1
                            product_old_content, product_new_content = get_modified_files.get_file_content(commit_hash, product_files_path)
                            test_old_content, test_new_content = get_modified_files.get_file_content(positive_related_commit, filter_changed_files)
                            # if gumtree_filter(product_old_content, product_new_content) and gumtree_filter(test_old_content, test_new_content):
                            json_block = {
                                "tag": "positive",
                                "product_commit": commit_hash,
                                "test_commit": positive_related_commit,
                                "product_file_path": product_files_path,
                                "test_file_path": filter_changed_files,
                                "product_old_content": product_old_content,
                                "product_new_content": product_new_content,
                                "test_old_content": test_old_content,
                                "test_new_content": test_new_content
                            }
                            save_PT_pair(json_block, os.path.join(output_dir, "samples.jsonl"))
                        
            if negative_related_commits is not None:
                for negative_related_commit in negative_related_commits:
                    related_changed_files = get_modified_files.get_changed_files(negative_related_commit)
                    for product_files_path in product_files_paths:
                        filter_changed_files = ""
                        for related_changed_file in related_changed_files:
                            if test_product_code_filter(related_changed_file, product_files_path):
                                filter_changed_files = related_changed_file
                                break
                        if filter_changed_files != "":
                            # print("find a negative sample")
                            negative_total += 1
                            product_old_content, product_new_content = get_modified_files.get_file_content(commit_hash, product_files_path)
                            test_old_content, test_new_content = get_modified_files.get_file_content(negative_related_commit, filter_changed_files)
                            json_block = {
                                "tag": "negative",
                                "product_commit": commit_hash,
                                "test_commit": negative_related_commit,
                                "product_file_path": product_files_path,
                                "test_file_path": filter_changed_files,
                                "product_old_content": product_old_content,
                                "product_new_content": product_new_content,
                                "test_old_content": test_old_content,
                                "test_new_content": test_new_content
                            }
                            save_PT_pair(json_block, os.path.join(output_dir, "samples.jsonl"))
                        
    print(f"positive_total: {positive_total}")
    print(f"negative_total: {negative_total}")



if __name__ == "__main__":

    # project_path = "/Users/mac/Desktop/Java"
    # project_path = "/Users/mac/Desktop/commons-math" # mac
    project_path = "/home/yeren/java-project/jfreechart"
    commit_hash_list = json.loads(handle_git_log.handle_git_log(project_path))
    # output_dir = "/Users/mac/Desktop/TestEvolution/common-math_output" # mac
    output_dir = "/home/yeren/TestEvolution/jfreechart_output"
    construct_PT_pair(project_path, output_dir, commit_hash_list)
    # print(gumtree_filter(a, b))
