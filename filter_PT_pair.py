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

def read_json(file):
    with open(file, 'r') as f:
        data = json.load(f)
    return data

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
            if product_file_path in file or test_file_path in file:
                return True
    os.chdir(current_path)
    return False

def line_col_to_char_index(text, start_line, start_column, end_line, end_column):
    lines = text.split('\n')
    start_index = sum(len(lines[i]) + 1 for i in range(start_line - 1)) + start_column - 1
    end_index = sum(len(lines[i]) + 1 for i in range(end_line - 1)) + end_column - 1
    return start_index, end_index



def strategy_1(json_block, product_change_actions, test_change_actions, project_path):
    # strategy 1: The type of the associated production code change or the test code change is non-modification type 
    # and there are no production/test changes between their commits: "NEGATIVE"--> “POSITIVE.”
    global n2p
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
    n2p += 1

def strategy_2(json_block, project_path):
    # strategy 2: There are additional production code modifications 
    # between production codechange commit and test code change commit: "POSITIVE" --> “NEGATIVE.”
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
        p2n += 1

def strategy_3(json_block, product_change_actions, test_change_actions):
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
    product_imports = []
    test_imports = []
    for product_change_action in product_change_actions:
        product_tree = product_change_action["tree"]
        if product_tree.startswith("ImportDeclaration"):
            start_line, end_line = extract_start_end_line(product_tree)
            import_content = product_old_content[start_line:end_line]
            if "import" in import_content:
                product_imports.append(import_content)
            import_content = product_new_content[start_line:end_line]
            if "import" in import_content:
                product_imports.append(import_content)
        if product_tree.startswith("QualifiedName"):
            start_line, end_line = extract_start_end_line(product_tree)
            if start_line < 7:
                continue
            import_content = product_old_content[start_line - 7:end_line + 1] 
            if "import" in import_content:
                product_imports.append(import_content)
            import_content = product_new_content[start_line - 7:end_line + 1]
            if "import" in import_content:
                product_imports.append(import_content)
    for test_change_action in test_change_actions:
        test_tree = test_change_action["tree"]
        if test_tree.startswith("ImportDeclaration"):
            start_line, end_line = extract_start_end_line(test_tree)
            import_content = test_old_content[start_line:end_line]
            if "import" in import_content:
                test_imports.append(import_content)
            import_content = test_new_content[start_line:end_line]
            if "import" in import_content:
                test_imports.append(import_content)
        if test_tree.startswith("QualifiedName"):
            start_line, end_line = extract_start_end_line(test_tree)
            if start_line < 7:
                continue
            import_content = test_old_content[start_line - 7:end_line] 
            if "import" in import_content:
                test_imports.append(import_content)
            import_content = test_new_content[start_line - 7:end_line]
            if "import" in import_content:
                test_imports.append(import_content)
    product_imports_set = set(product_imports)
    test_imports_set = set(test_imports)
    if product_imports_set.intersection(test_imports_set) == set():
        json_block["tag"] = "negative"
        p2n += 1

def strategy_4(json_block, product_change_actions, test_change_actions):
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

    product_changes = []
    test_changes = []
    for product_change_action in product_change_actions:
        product_tree = product_change_action["tree"]
        start_line, end_line = extract_start_end_line(product_tree)
        if start_line is not None:
            content = product_old_content[start_line:end_line]
            product_changes.extend(re.split(r'[ ,;{}\[\]()\.\+=:"]+', content))
            content = product_new_content[start_line:end_line]
            product_changes.extend(re.split(r'[ ,;{}\[\]()\.\+=:"]+', content))
    for test_change_action in test_change_actions:
        test_tree = test_change_action["tree"]
        start_line, end_line = extract_start_end_line(test_tree)
        if start_line is not None:
            content = test_old_content[start_line:end_line]
            test_changes.extend(re.split(r'[ ,;{}\[\]()\.\+=:"]+', content))
            content = test_new_content[start_line:end_line]
            test_changes.extend(re.split(r'[ ,;{}\[\]()\.\+=:"]+', content))
    product_changes_set = set(product_changes)
    test_changes_set = set(test_changes)
    if product_changes_set.intersection(test_changes_set) == set():
        json_block["tag"] = "negative"
        p2n += 1

def strategy_5(json_block, product_change_actions, test_change_actions, refactorings):
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
        p2n += 1
    

if __name__ == "__main__":
    input_dir = "/Users/mac/Desktop/TestEvolution/common-math_output"
    project_path = "/Users/mac/Desktop/commons-math"
    current_path = os.getcwd()
    old_path = os.path.join(temp_folder, "temp_old.java")
    new_path = os.path.join(temp_folder, "temp_new.java")
    target_path = os.path.join(temp_folder, "temp_target.json")
    refactoring_path = os.path.join(temp_folder, "temp_refactoring.json")
    data = read_json(input_dir + "/samples.json")
    for json_block in tqdm(data):
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
        product_change_actions = read_json(target_path)["actions"]
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
        test_change_actions = read_json(target_path)["actions"]
        
        command = f"./RefactoringMiner-3.0.4/bin/RefactoringMiner -c {project_path} {test_commit} -json {refactoring_path}"
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
            # return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # print(f"Error running command {' '.join(command)}: {e}")
            logging.error(f"Error running command {' '.join(command)}: {e}")
            continue
        refactorings = read_json(refactoring_path)["commits"][0]["refactorings"]

        if tag == "negative":
            strategy_1(json_block, product_change_actions, test_change_actions, project_path)
        else:
            strategy_2(json_block, project_path)
            strategy_3(json_block, product_change_actions, test_change_actions)
            strategy_4(json_block, product_change_actions, test_change_actions)
            strategy_5(json_block, product_change_actions, test_change_actions, refactorings)

    print("p2n: ", p2n)
    print("n2p: ", n2p)





