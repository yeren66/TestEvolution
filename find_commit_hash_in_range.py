import subprocess
import sys
from datetime import datetime, timedelta
import os

def run_git_command(command):
    """运行 Git 命令并返回输出"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command)}: {e}")
        return None

def get_commit_date(commit_hash):
    """获取指定 commit 的提交日期"""
    command = ["git", "show", "-s", "--format=%ci", commit_hash]
    commit_date_str = run_git_command(command)
    if commit_date_str:
        return datetime.strptime(commit_date_str, "%Y-%m-%d %H:%M:%S %z")
    else:
        return None

def find_commits_after_date(start_date, end_date=None):
    """查找在指定日期之后（和可选的结束日期之前）的所有 commits"""
    date_format = "%Y-%m-%d %H:%M"
    since_date_str = start_date.strftime(date_format)
    command = ["git", "log", "--after", since_date_str, "--format=%H"]
    if end_date:
        until_date_str = end_date.strftime(date_format)
        command.extend(["--before", until_date_str])
    return run_git_command(command).split('\n')

def find_commits(commit_hash, hours_after, hours_until=None):
    start_date = get_commit_date(commit_hash)
    if not start_date:
        print(f"Could not find commit {commit_hash}")
        return
    
    end_date = None
    if hours_until:
        end_date = start_date + timedelta(hours=hours_until)
    start_date += timedelta(hours=hours_after)
    
    commits = find_commits_after_date(start_date, end_date)
    # print(f"Commits after {hours_after} hours (and within {hours_until} hours, if specified):")
    if hours_after != 0 and commit_hash in commits:
        # itself is not included when hours_after is not 0
        commits.remove(commit_hash)
    if hours_after == 0 and commit_hash not in commits:
        commits.append(commit_hash)
    commits.reverse()
    # for commit in commits:
    #     print(commit)
    return commits

if __name__ == "__main__":
    # if len(sys.argv) < 3 or len(sys.argv) > 4:
    #     print("Usage: python script.py <commit_hash> <hours_after> [<hours_until>]")
    #     sys.exit(1)
    # commit_hash = sys.argv[1]
    # hours_after = int(sys.argv[2])
    # hours_until = int(sys.argv[3]) if len(sys.argv) == 4 else None
    # main(commit_hash, hours_after, hours_until)

    path = "/Users/mac/Desktop/Java"
    os.chdir(path)

    # commit_hash = '05ca93eace893a75e886a19739778a67bd3a18bc'
    commit_hash = '14b3f45f9f32df108de5d0eace624f23d6bbe1bf'
    hours_after = 0
    hours_until = 1200
    find_commits(commit_hash, hours_after, hours_until)
