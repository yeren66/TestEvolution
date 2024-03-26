import json
import subprocess
import logging
import find_commit_hash_in_range
import get_modified_files
import re
import os
from tqdm import tqdm

temp_folder = "temp"
p2n = 0
n2p = 0
logging.basicConfig(filename="filter_PT_pair.log", level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def run_git_command(command):
    """运行 Git 命令并返回输出"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # print(f"Error running command {' '.join(command)}: {e}")
        logging.error(f"Error running command {' '.join(command)}: {e}")
        return None

def read_json_low(file):
    with open(file, 'r') as f:
        data = json.load(f)
    return data

def read_json(file_path):
    PT_pairs = []
    with open(file_path, 'r') as file:
        for line in file:
            PT_pairs.append(json.loads(line.strip()))
    return PT_pairs

def extract_start_end_line(text):
    pattern = r"\[(\d+),(\d+)\]"
    # Search for the pattern in the text
    match = re.search(pattern, text)
    # Extract the last two numbers if the pattern is found
    if match:
        start_line, end_line = match.groups()
        return int(start_line), int(end_line)
    else:
        return None, None
    

def related_files_between_commits(old_commit, new_commit, project_path, product_file_path, test_file_path):
    # 判断两个commit之间是否有其他commit修改了生产/测试相关的文件
    # 如果有，则返回True；否则返回False
    # 若只需要判断生产/测试其中之一，则将另一个参数置为“”(空字符串)
    if old_commit == new_commit:
        return False
    current_path = os.getcwd()
    os.chdir(project_path)
    old_time = find_commit_hash_in_range.get_commit_date(old_commit)
    new_time = find_commit_hash_in_range.get_commit_date(new_commit)
    related_commits = find_commit_hash_in_range.find_commits(old_commit, 0, (new_time - old_time).seconds / 3600)
    if old_commit in related_commits:
        related_commits.remove(old_commit)
    if new_commit in related_commits:
        related_commits.remove(new_commit)
    for commit in related_commits:
        changed_files = get_modified_files.get_changed_files(commit)
        for file in changed_files:
            if product_file_path == file or test_file_path == file:
                os.chdir(current_path)
                return True
    # 对old_commit和new_commit单独进行判断，观察old_commit中是否有test_file_path，new_commit中是否有product_file_path
    old_changed_files = get_modified_files.get_changed_files(old_commit)
    new_changed_files = get_modified_files.get_changed_files(new_commit)
    for file in old_changed_files:
        if test_file_path == file:
            os.chdir(current_path)
            return True
    for file in new_changed_files:
        if product_file_path == file:
            os.chdir(current_path)
            return True
    os.chdir(current_path)
    return False

def line_col_to_char_index(text, start_line, start_column, end_line, end_column):
    lines = text.split('\n')
    # 确保行号不会超出文本的实际行数
    start_line = max(1, min(start_line, len(lines)))
    end_line = max(1, min(end_line, len(lines)))

    # 计算起始索引，如果起始列超过该行的长度，则将其限制在行的最大长度
    start_index = sum(len(lines[i]) + 1 for i in range(start_line - 1))
    start_index += min(start_column - 1, len(lines[start_line - 1]))

    # 计算结束索引，同样如果结束列超过该行的长度，则将其限制在行的最大长度
    end_index = sum(len(lines[i]) + 1 for i in range(end_line - 1))
    end_index += min(end_column - 1, len(lines[end_line - 1]))

    return start_index, end_index



def strategy_1(json_block, product_change_actions, test_change_actions, project_path):
    # strategy 1: The type of the associated production code change or the test code change is non-modification type 
    # and there are no production/test changes between their commits: "NEGATIVE"--> “POSITIVE.”
    global n2p, change_type_set
    if json_block["tag"] == "positive":
        return 
    product_commit = json_block["product_commit"]
    test_commit = json_block["test_commit"]
    product_file_path = json_block["product_file_path"]
    test_file_path = json_block["test_file_path"]
    product_old_content = json_block["product_old_content"]
    product_new_content = json_block["product_new_content"]
    test_old_content = json_block["test_old_content"]
    test_new_content = json_block["test_new_content"]

    if product_change_actions == [] or test_change_actions == []:
        return
    # 判断两个commit之间是否有其他commit修改了生产/测试相关的文件
    if related_files_between_commits(product_commit, test_commit, project_path, product_file_path, test_file_path):
        return 
    # 判断两个文件的更改内容是否仅为添加或删除（非修改内容，也即非update和move）
    # 注 -- gumtree的修改类型有四种：insert, delete, update, move
    for change_action in product_change_actions:
        change_type = change_action["action"].split("-")[0]
        if change_type == "update" or change_type == "move":
            return
    for change_action in test_change_actions:
        change_type = change_action["action"].split("-")[0]
        if change_type == "update" or change_type == "move":
            return
    json_block["tag"] = "positive"
    current_path = os.getcwd()
    os.chdir(project_path)
    product_time = find_commit_hash_in_range.get_commit_date(product_commit)
    test_time = find_commit_hash_in_range.get_commit_date(test_commit)
    os.chdir(current_path)
    logging.info(f"No.{n2p + 1} negative --> positive\nproduct_commit: {product_commit}\ntest_commit: {test_commit}\nproduct_time: {product_time}\ntest_time: {test_time}\nproduct_file_path: {product_file_path}\ntest_file_path: {test_file_path}")
    n2p += 1

def strategy_2(json_block, project_path):
    # strategy 2: There are additional production code modifications 
    # between production code change commit and test code change commit: "POSITIVE" --> “NEGATIVE.”
    global p2n
    if json_block["tag"] == "negative":
        return
    product_commit = json_block["product_commit"]
    test_commit = json_block["test_commit"]
    product_file_path = json_block["product_file_path"]
    test_file_path = json_block["test_file_path"]
    product_old_content = json_block["product_old_content"]
    product_new_content = json_block["product_new_content"]
    test_old_content = json_block["test_old_content"]
    test_new_content = json_block["test_new_content"]
    if related_files_between_commits(product_commit, test_commit, project_path, product_file_path, ""):
        json_block["tag"] = "negative"
        current_path = os.getcwd()
        os.chdir(project_path)
        product_time = find_commit_hash_in_range.get_commit_date(product_commit)
        test_time = find_commit_hash_in_range.get_commit_date(test_commit)
        os.chdir(current_path)
        logging.info(f"No.{p2n + 1} positive --> negative by strategy 2\nproduct_commit: {product_commit}\ntest_commit: {test_commit}\nproduct_time: {product_time}\ntest_time: {test_time}\nproduct_file_path: {product_file_path}\ntest_file_path: {test_file_path}")
        
        p2n += 1

def strategy_3(json_block, product_change_actions, test_change_actions, project_path):
    # strategy 3: The changes of the production or test code involve only import changes, 
    # and the intersection of import modification is empty: "POSITIVE" --> “NEGATIVE.”
    global p2n
    if json_block["tag"] == "negative":
        return
    product_commit = json_block["product_commit"]
    test_commit = json_block["test_commit"]
    product_file_path = json_block["product_file_path"]
    test_file_path = json_block["test_file_path"]
    product_old_content = json_block["product_old_content"]
    product_new_content = json_block["product_new_content"]
    test_old_content = json_block["test_old_content"]
    test_new_content = json_block["test_new_content"]
    product_imports = set()
    test_imports = set()
    for product_change_action in product_change_actions:
        product_tree = product_change_action["tree"]
        action = product_change_action["action"].split("-")[0]
        if (not product_tree.startswith("ImportDeclaration")) and (not product_tree.startswith("QualifiedName")):
            return 
        
        if product_tree.startswith("ImportDeclaration"):
            start_line, end_line = extract_start_end_line(product_tree)
            if action != "insert":
                import_content = product_old_content[start_line:end_line]
                if "import" in import_content:
                    product_imports.add(import_content)
            else:
                import_content = product_new_content[start_line:end_line]
                if "import" in import_content:
                    product_imports.add(import_content)
        if product_tree.startswith("QualifiedName"):
            start_line, end_line = extract_start_end_line(product_tree)
            if start_line < 7:
                continue
            if action != "insert":
                import_content = product_old_content[start_line - 7:end_line + 1] 
                if "import" in import_content:
                    product_imports.add(import_content)
            else:
                import_content = product_new_content[start_line - 7:end_line + 1]
                if "import" in import_content:
                    product_imports.add(import_content)
    for test_change_action in test_change_actions:
        test_tree = test_change_action["tree"]
        action = test_change_action["action"].split("-")[0]
        if (not test_tree.startswith("ImportDeclaration")) and (not test_tree.startswith("QualifiedName")):
            return
        if test_tree.startswith("ImportDeclaration"):
            start_line, end_line = extract_start_end_line(test_tree)
            if action != "insert":
                import_content = test_old_content[start_line:end_line]
                if "import" in import_content:
                    test_imports.add(import_content)
            else:
                import_content = test_new_content[start_line:end_line]
                if "import" in import_content:
                    test_imports.add(import_content)
        if test_tree.startswith("QualifiedName"):
            start_line, end_line = extract_start_end_line(test_tree)
            if start_line < 7:
                continue
            if action != "insert":
                import_content = test_old_content[start_line - 7:end_line + 1] 
                if "import" in import_content:
                    test_imports.add(import_content)
            else:
                import_content = test_new_content[start_line - 7:end_line + 1]
                if "import" in import_content:
                    test_imports.add(import_content)

    if product_imports.intersection(test_imports) == set():
        json_block["tag"] = "negative"
        current_path = os.getcwd()
        os.chdir(project_path)
        product_time = find_commit_hash_in_range.get_commit_date(product_commit)
        test_time = find_commit_hash_in_range.get_commit_date(test_commit)
        os.chdir(current_path)
        logging.info(f"No.{p2n + 1} positive --> negative by strategy 3\nproduct_commit: {product_commit}\ntest_commit: {test_commit}\nproduct_time: {product_time}\ntest_time: {test_time}\nproduct_file_path: {product_file_path}\ntest_file_path: {test_file_path}")
        
        p2n += 1

def strategy_4(json_block, product_change_actions, test_change_actions, project_path):
    # strategy 4: There is no semantic relevance between the changes of the production and testcode. "POSITIVE" --> “NEGATIVE.”
    global p2n
    if json_block["tag"] == "negative":
        return
    product_commit = json_block["product_commit"]
    test_commit = json_block["test_commit"]
    product_file_path = json_block["product_file_path"]
    test_file_path = json_block["test_file_path"]
    product_old_content = json_block["product_old_content"]
    product_new_content = json_block["product_new_content"]
    test_old_content = json_block["test_old_content"]
    test_new_content = json_block["test_new_content"]

    product_changes = set()
    test_changes = set()
    for product_change_action in product_change_actions:
        if "parent" in product_change_action:
            product_tree = product_change_action["parent"]
        else:
            product_tree = product_change_action["tree"]
        action = product_change_action["action"].split("-")[0]
        start_line, end_line = extract_start_end_line(product_tree)
        if start_line is not None:
            if action != "insert":
                content = product_old_content[start_line:end_line]
                product_changes.update(re.split(r'[ @\n\\/,;{}\[\]()\.\+=:"]+', content))
            else:
                content = product_new_content[start_line:end_line]
                product_changes.update(re.split(r'[ @\n\\/,;{}\[\]()\.\+=:"]+', content))
    for test_change_action in test_change_actions:
        if "parent" in test_change_action:
            test_tree = test_change_action["parent"]
        else:
            test_tree = test_change_action["tree"]
        action = test_change_action["action"].split("-")[0]
        start_line, end_line = extract_start_end_line(test_tree)
        if start_line is not None:
            if action != "insert":
                content = test_old_content[start_line:end_line]
                test_changes.update(re.split(r'[ @\n\\/,;{}\[\]()\.\+=:"]+', content))
            else:
                content = test_new_content[start_line:end_line]
                test_changes.update(re.split(r'[ @\n\\/,;{}\[\]()\.\+=:"]+', content))
    product_changes_set = set(product_changes)
    test_changes_set = set(test_changes)
    if product_changes_set.intersection(test_changes_set) == set():
        json_block["tag"] = "negative"
        current_path = os.getcwd()
        os.chdir(project_path)
        product_time = find_commit_hash_in_range.get_commit_date(product_commit)
        test_time = find_commit_hash_in_range.get_commit_date(test_commit)
        os.chdir(current_path)
        logging.info(f"No.{p2n + 1} positive --> negative by strategy 4\nproduct_commit: {product_commit}\ntest_commit: {test_commit}\nproduct_time: {product_time}\ntest_time: {test_time}\nproduct_file_path: {product_file_path}\ntest_file_path: {test_file_path}")
        
        p2n += 1

def strategy_5(json_block, product_change_actions, test_change_actions, refactorings, project_path):
    # strategy 5: The type of modification involves annotations, modifiers, and refactoring op-erations: "POSITIVE" --> “NEGATIVE.”
    global p2n
    if json_block["tag"] == "negative":
        return
    product_commit = json_block["product_commit"]
    test_commit = json_block["test_commit"]
    product_file_path = json_block["product_file_path"]
    test_file_path = json_block["test_file_path"]
    product_old_content = json_block["product_old_content"]
    product_new_content = json_block["product_new_content"]
    test_old_content = json_block["test_old_content"]
    test_new_content = json_block["test_new_content"]

    # product_changes = []
    test_changes = []

    for product_change_action in product_change_actions:
        product_tree = product_change_action["tree"]
        if "Annotation" in product_tree or product_tree.startswith("Modifier"):
            continue
        else:
            return
    for test_change_action in test_change_actions:
        test_tree = test_change_action["tree"]
        if "Annotation" in test_tree or test_tree.startswith("Modifier"):
            continue
        start_line, end_line = extract_start_end_line(test_tree)
        test_changes.append((start_line, end_line))
    if test_changes == []:
        json_block["tag"] = "negative"
        current_path = os.getcwd()
        os.chdir(project_path)
        product_time = find_commit_hash_in_range.get_commit_date(product_commit)
        test_time = find_commit_hash_in_range.get_commit_date(test_commit)
        os.chdir(current_path)
        logging.info(f"No.{p2n + 1} positive --> negative by strategy 5\nproduct_commit: {product_commit}\ntest_commit: {test_commit}\nproduct_time: {product_time}\ntest_time: {test_time}\nproduct_file_path: {product_file_path}\ntest_file_path: {test_file_path}")
        
        p2n += 1
        return
    for refactoring in refactorings:
        for location in refactoring["leftSideLocations"]:
            start_line = location["startLine"]
            end_line = location["endLine"]
            start_column = location["startColumn"]
            end_column = location["endColumn"]
            start_index, end_index = line_col_to_char_index(test_old_content, start_line, start_column, end_line, end_column)
            test_changes[:] = [change for change in test_changes if not (start_index <= change[0] and end_index >= change[1])]
    if test_changes == []:
        json_block["tag"] = "negative"
        current_path = os.getcwd()
        os.chdir(project_path)
        product_time = find_commit_hash_in_range.get_commit_date(product_commit)
        test_time = find_commit_hash_in_range.get_commit_date(test_commit)
        os.chdir(current_path)
        logging.info(f"No.{p2n + 1} positive --> negative by strategy 5\nproduct_commit: {product_commit}\ntest_commit: {test_commit}\nproduct_time: {product_time}\ntest_time: {test_time}\nproduct_file_path: {product_file_path}\ntest_file_path: {test_file_path}")
        
        p2n += 1


def strategy_6(json_block, product_change_actions, test_change_actions, project_path):
    # strategy 6: customize rule, remove the positive part with only comment change. "POSITIVE" --> “NEGATIVE.”
    global p2n
    
    product_commit = json_block["product_commit"]
    test_commit = json_block["test_commit"]
    product_file_path = json_block["product_file_path"]
    test_file_path = json_block["test_file_path"]
    product_old_content = json_block["product_old_content"]
    product_new_content = json_block["product_new_content"]
    test_old_content = json_block["test_old_content"]
    test_new_content = json_block["test_new_content"]
    
    if product_old_content == None or product_new_content == None or test_old_content == None or test_new_content == None:
        return True
    if json_block["tag"] == "negative":
        return False

    if product_change_actions == [] or test_change_actions == []:
        # json_block["tag"] = "negative"
        current_path = os.getcwd()
        os.chdir(project_path)
        product_time = find_commit_hash_in_range.get_commit_date(product_commit)
        test_time = find_commit_hash_in_range.get_commit_date(test_commit)
        os.chdir(current_path)
        logging.info(f"No.{p2n + 1} positive --> negative by strategy 6\nproduct_commit: {product_commit}\ntest_commit: {test_commit}\nproduct_time: {product_time}\ntest_time: {test_time}\nproduct_file_path: {product_file_path}\ntest_file_path: {test_file_path}\n")
        
        # p2n += 1
        return True

    for product_change_action in product_change_actions:
        product_tree = product_change_action["tree"].split(":")[0]
        if product_tree != "TextElement":
            return False
        
    for test_change_action in test_change_actions:
        test_tree = test_change_action["tree"].split(":")[0]
        if test_tree != "TextElement":
            return False
        
    # json_block["tag"] = "negative"
    current_path = os.getcwd()
    os.chdir(project_path)
    product_time = find_commit_hash_in_range.get_commit_date(product_commit)
    test_time = find_commit_hash_in_range.get_commit_date(test_commit)
    os.chdir(current_path)  
    logging.info(f"No.{p2n + 1} positive --> negative by strategy 6\nproduct_commit: {product_commit}\ntest_commit: {test_commit}\nproduct_time: {product_time}\ntest_time: {test_time}\nproduct_file_path: {product_file_path}\ntest_file_path: {test_file_path}")
        
    # p2n += 1
    return True


    

if __name__ == "__main__":
    # input_dir = "/Users/mac/Desktop/TestEvolution/common-math_output" # mac
    input_dir = "/home/yeren/TestEvolution/nrtsearch_output"
    output_dir = "/home/yeren/TestEvolution/nrtsearch_output"
    # project_path = "/Users/mac/Desktop/commons-math" # mac
    project_path = "/home/yeren/java-project/nrtsearch"
    current_path = os.getcwd()
    old_path = os.path.join(temp_folder, "temp_old.java")
    new_path = os.path.join(temp_folder, "temp_new.java")
    target_path = os.path.join(temp_folder, "temp_target.json")
    refactoring_path = os.path.join(temp_folder, "temp_refactoring.json")
    data = read_json(input_dir + "/samples.jsonl")

    index_with_not_delete = []
    delete_number = 0

    for index, json_block in tqdm(enumerate(data), total=len(data)):
        os.chdir(current_path)
        tag = json_block["tag"]
        product_commit = json_block["product_commit"]
        test_commit = json_block["test_commit"]
        product_file_path = json_block["product_file_path"]
        test_file_path = json_block["test_file_path"]
        product_old_content = json_block["product_old_content"]
        product_new_content = json_block["product_new_content"]
        test_old_content = json_block["test_old_content"]
        test_new_content = json_block["test_new_content"]

        # debug
        # if product_commit != "1458a9366aa9a001e25153f669a9a5bb8235a30b" or test_commit != "1458a9366aa9a001e25153f669a9a5bb8235a30b":
        #     continue
        # if product_file_path != "apollo-portal/src/main/java/com/ctrip/framework/apollo/portal/controller/UserInfoController.java" or test_file_path != "apollo-portal/src/test/java/com/ctrip/framework/apollo/portal/controller/UserInfoControllerTest.java":
        #     continue

        if product_old_content == None or product_new_content == None or test_old_content == None or test_new_content == None:
            json_block["tag"] = "negative"
            continue

        # print(os.getcwd())
        with open(old_path, "w") as file:
            file.write(product_old_content)
        with open(new_path, "w") as file:
            file.write(product_new_content)
        command = f"java -jar gumtree.jar textdiff {old_path} {new_path} -f JSON -o {target_path}"
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
            # return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # print(f"Error running command {' '.join(command)}: {e}")
            logging.error(f"Error running command {' '.join(command)}: {e}")
            continue
        product_change_actions = read_json_low(target_path)["actions"]
        with open(old_path, "w") as file:
            file.write(test_old_content)
        with open(new_path, "w") as file:
            file.write(test_new_content)
        command = f"java -jar gumtree.jar textdiff {old_path} {new_path} -f JSON -o {target_path}"
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
            # return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # print(f"Error running command {' '.join(command)}: {e}")
            logging.error(f"Error running command {' '.join(command)}: {e}")
            continue
        test_change_actions = read_json_low(target_path)["actions"]
        
        command = f"./RefactoringMiner-3.0.4/bin/RefactoringMiner -c {project_path} {test_commit} -json {refactoring_path}"
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
            # return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # print(f"Error running command {' '.join(command)}: {e}")
            logging.error(f"Error running command {' '.join(command)}: {e}")
            continue
        refactorings = read_json_low(refactoring_path)["commits"][0]["refactorings"]

        if tag == "negative":
            strategy_1(json_block, product_change_actions, test_change_actions, project_path)
            index_with_not_delete.append(index)
        else:
            whether_delete = strategy_6(json_block, product_change_actions, test_change_actions, project_path)
            if not whether_delete:
                index_with_not_delete.append(index)
            else:
                delete_number += 1
                continue
            strategy_2(json_block, project_path)
            strategy_3(json_block, product_change_actions, test_change_actions, project_path)
            strategy_4(json_block, product_change_actions, test_change_actions, project_path)
            strategy_5(json_block, product_change_actions, test_change_actions, refactorings, project_path)

    print("p2n: ", p2n)
    print("n2p: ", n2p)
    print("delete_number: ", delete_number)
    filter_data = [data[i] for i in index_with_not_delete]
    with open(output_dir + "/filter.json", 'w') as file:
        json.dump(filter_data, file, indent=4)



