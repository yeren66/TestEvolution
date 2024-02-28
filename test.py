import json
import subprocess
import os
import difflib

output_path = "manual_watch"
if not os.path.exists(output_path):
    os.makedirs(output_path)

positive_sample_path = "common-math_output2/positive_samples.json"
negative_sample_path = "common-math_output2/negative_samples.json"
with open(positive_sample_path, "r") as file:
    positive_samples = json.load(file)

# project_path = "/Users/mac/Desktop/commons-math"
# os.chdir(project_path)

index = 0
for index in range(len(positive_samples)):
    product_commit = positive_samples[index]["product_commit"]
    test_commit = positive_samples[index]["test_commit"]
    product_file_path = positive_samples[index]["product_file_path"]
    test_file_path = positive_samples[index]["test_file_path"]
    product_old_content = positive_samples[index]["product_old_content"]
    product_new_content = positive_samples[index]["product_new_content"]
    test_old_content = positive_samples[index]["test_old_content"]
    test_new_content = positive_samples[index]["test_new_content"]

    def run_git_command(command):
        """运行 Git 命令并返回输出"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running command {' '.join(command)}: {e}")
            return None
        
    # product_change = run_git_command(["git", "show", f"{product_commit}:{product_file_path}"])
    # test_change = run_git_command(["git", "diff", f"{test_commit}^ {test_commit} -- {test_file_path}"])
        
    try:
        diff = difflib.unified_diff(product_old_content.splitlines(), product_new_content.splitlines(), lineterm='')
        product_change = '\n'.join(list(diff))

        diff = difflib.unified_diff(test_old_content.splitlines(), test_new_content.splitlines(), lineterm='')
        test_change = '\n'.join(list(diff))

        with open(os.path.join(output_path, str(index) + "_product_change.diff"), "w") as file:
            file.write(product_change)
        with open(os.path.join(output_path, str(index) + "_test_change.diff"), "w") as file:
            file.write(test_change)
    except Exception as e:
        print(e)
        print(f"Error running command: {product_commit} {test_commit} {product_file_path} {test_file_path}")
        continue
