import json
import re
from datetime import datetime

def parse_git_log(file_path):
    with open(file_path, 'r') as file:
        log_text = file.read()

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

    return commits

# 解析日志文件
log_file_path = 'git_log_mac.txt'
parsed_commits = parse_git_log(log_file_path)

# 转换为JSON
json_output = json.dumps(parsed_commits, indent=4)

# 输出到JSON文件
output_json_path = 'parsed_git_log_mac.json'
with open(output_json_path, 'w') as json_file:
    json_file.write(json_output)

output_json_path

