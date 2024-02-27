import subprocess
import re
import os
import json

def get_commit_changes(commit_hash, project_path):

    os.chdir(project_path)

    # 执行 git show [commit-hash] 命令
    process = subprocess.Popen(["git", "show", commit_hash], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f"Error: {stderr.decode('utf-8')}")
        return []

    # 解析输出，获取每个文件的变更
    commit_content = stdout.decode("utf-8")
    diffs = re.split(r'diff --git', commit_content)[1:]  # 分割每个文件的更改
    changes = []

    for diff in diffs:
        # 解析每个文件的路径和更改内容
        file_path_match = re.search(r'a/(.+?) b/.+?\n', diff)
        if not file_path_match:
            continue
        file_path = file_path_match.group(1)
        change_content = diff.split('\n')[1:]  # 更改内容从第二行开始

        # 获取修改前的文件内容
        process = subprocess.Popen(["git", "show", f"{commit_hash}^:{file_path}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()
        old_content = stdout.decode("utf-8")

        # TODO: 应用更改到 old_content 上以获取新内容
        # 这是一个复杂的任务，可能需要详细的文本处理逻辑
        new_content = old_content  # 这里需要替换为正确的逻辑

        changes.append({
            'commit': commit_hash,
            'file_path': file_path,
            'old_content': old_content,
            'new_content': new_content
        })

    return changes

# 示例使用
current_path = os.getcwd()
# project_path = '/home/yeren/java-project/Java'  # omen
project_path = "/Users/mac/Desktop/Java"  # mac

commit_hash = '05ca93eace893a75e886a19739778a67bd3a18bc'  # 替换为实际的commit哈希值
changes = get_commit_changes(commit_hash, project_path)

os.chdir(current_path)
with open('changes.json', 'w') as file:
    file.write(json.dumps(changes, indent=4))

print(changes)
