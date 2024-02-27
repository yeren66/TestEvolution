import json
import os
import get_modified_files
import find_commit_hash_in_range
import re
from tqdm import tqdm

def read_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)
    

def product_code_filter(changed_file_path):
    key_words = ["src/main/java", ".java"]
    for key_word in key_words:
        if key_word not in changed_file_path:
            return False
    return True

def test_product_code_filter(change_file_path, related_product_file_path):
    # test_file_name = change_file_path.split('/')[-1]
    # if 'test' not in test_file_name.lower():
    #     return False
    path_info = '/'.join(related_product_file_path.split('/')[:-1])
    path_info = re.sub(r"src/main/java", "src/test/java", path_info)
    product_file_name = related_product_file_path.split('/')[-1].split('.')[0]
    key_words = [path_info, product_file_name]
    for key_word in key_words:
        if key_word not in change_file_path:
            return False
    return True

def save_PT_pair(json_block, output_file_path):
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r') as file:
            PT_pairs = json.load(file)
    else:
        PT_pairs = []
    PT_pairs.append(json_block)
    with open(output_file_path, 'w') as file:
        json.dump(PT_pairs, file, indent=4)


def construct_PT_pair(project_path, output_dir, commit_info_list):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 切换至对应的项目目录
    os.chdir(project_path)
    # 遍历从该项目下获取的每个commit
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
            # 正样本中，筛选出时间上离该commit最近的test code文件；负样本则全部保留
            for product_files_path in product_files_paths:
                for positive_related_commit in positive_related_commits:
                    related_changed_files = get_modified_files.get_changed_files(positive_related_commit)
                    filter_changed_files = []
                    for related_changed_file in related_changed_files:
                        if test_product_code_filter(related_changed_file, product_files_path):
                            filter_changed_files.append(related_changed_file)
                    related_changed_files = filter_changed_files
                    if len(related_changed_files) == 1:
                        print("find a positive sample")
                        product_old_content, product_new_content = get_modified_files.get_file_content(commit_hash, product_files_path)
                        test_old_content, test_new_content = get_modified_files.get_file_content(positive_related_commit, related_changed_files[0])
                        json_block = {
                            "product_commit": commit_hash,
                            "test_commit": positive_related_commit,
                            "product_file_path": product_files_path,
                            "test_file_path": related_changed_files[0],
                            "product_old_content": product_old_content,
                            "product_new_content": product_new_content,
                            "test_old_content": test_old_content,
                            "test_new_content": test_new_content
                        }
                        save_PT_pair(json_block, os.path.join(output_dir, "positive_samples.json"))
                        break

                for negative_related_commit in negative_related_commits:
                    related_changed_files = get_modified_files.get_changed_files(negative_related_commit)
                    filter_changed_files = []
                    for related_changed_file in related_changed_files:
                        if test_product_code_filter(related_changed_file, product_files_path):
                            filter_changed_files.append(related_changed_file)
                    related_changed_files = filter_changed_files
                    if len(related_changed_files) == 1:
                        print("find a negative sample")
                        product_old_content, product_new_content = get_modified_files.get_file_content(commit_hash, product_files_path)
                        test_old_content, test_new_content = get_modified_files.get_file_content(negative_related_commit, related_changed_files[0])
                        json_block = {
                            "product_commit": commit_hash,
                            "test_commit": negative_related_commit,
                            "product_file_path": product_files_path,
                            "test_file_path": related_changed_files[0],
                            "product_old_content": product_old_content,
                            "product_new_content": product_new_content,
                            "test_old_content": test_old_content,
                            "test_new_content": test_new_content
                        }
                        save_PT_pair(json_block, os.path.join(output_dir, "negative_samples.json"))



if __name__ == "__main__":
    commit_hash_list = read_json('parsed_git_log_mac.json')
    project_path = "/Users/mac/Desktop/Java"
    output_dir = "/Users/mac/Desktop/TestEvolution/output2"
    construct_PT_pair(project_path, output_dir, commit_hash_list)