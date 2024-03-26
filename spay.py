import subprocess
import os
import json
import re
from datetime import datetime

def save_git_log_to_file(repo_path):
    # 保存当前目录路径
    original_path = os.getcwd()

    try:
        # 切换到Java项目的目录
        os.chdir(repo_path)

        # 使用subprocess调用git log命令
        process = subprocess.Popen(["git", "log"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 读取输出
        stdout, stderr = process.communicate()

        # 如果出错，打印错误信息
        if process.returncode != 0:
            os.chdir(original_path)
            print(f"Error: {stderr.decode('utf-8')}")
            return

    finally:
        # 无论如何都回到原来的目录
        os.chdir(original_path)

    return stdout.decode('utf-8')

def parse_git_log(log_text):

    commits = []
    # 使用正则表达式分割提交
    for commit_block in re.split(r'\ncommit ', log_text.strip()):
        if not commit_block.strip():
            continue
        lines = commit_block.split('\n')
        commit_hash = lines[0].strip()
        merge_line = None
        author_line = None
        date_line = None
        message_lines = []

        # 处理每行，提取必要信息
        for i, line in enumerate(lines[1:]):
            if line.startswith('Merge:'):
                merge_line = line.strip()
            elif line.startswith('Author:'):
                author_line = line.strip()
            elif line.startswith('Date:'):
                date_line = line.strip()
            elif i > 0:  # 消息开始于日期行之后
                message_lines.append(line.strip())

        # 提取作者和日期
        if author_line and date_line:
            author_match = re.search(r'Author: (.*)', author_line)
            date_match = re.search(r'Date:   (.*)', date_line)
            author = author_match.group(1) if author_match else None
            date_str = date_match.group(1).strip() if date_match else None

            # 转换日期字符串为日期对象
            try:
                date = datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y %z')
            except ValueError as e:
                print(f"Error parsing date: {date_str} - {e}")
                continue

            # 构建commit字典
            commit = {
                'commit': commit_hash,
                'merge': merge_line,
                'author': author,
                'date': date.isoformat(),
                'message': '\n'.join(message_lines)
            }

            commits.append(commit)

    json_output = json.dumps(commits, indent=4)

    return json_output

def handle_git_log(repo_path):
    log_text = save_git_log_to_file(repo_path)
    json_output = parse_git_log(log_text)
    return json_output

if __name__ == "__main__":
    repo_path = "/home/yeren/java-project/commons-math"
    json_output = handle_git_log(repo_path)
    output_json_path = 'parsed_git_log111.json'
    with open(output_json_path, 'w') as json_file:
        json_file.write(json_output)