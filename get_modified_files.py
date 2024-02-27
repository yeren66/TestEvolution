import subprocess
import os
import sys

def run_git_command(command):
    """运行 Git 命令并返回输出"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command)}: {e}")
        return None

def get_changed_files(commit_hash):
    """获取指定 commit 修改的文件列表"""
    command = ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash]
    output = run_git_command(command)
    if output:
        return output.split('\n')
    else:
        return []

def get_file_content(commit_hash, file_path):
    """保存指定 commit 中文件的内容到目录中"""
    old_file_content = run_git_command(["git", "show", f"{commit_hash}^:{file_path}"])
    new_file_content = run_git_command(["git", "show", f"{commit_hash}:{file_path}"])
    if old_file_content is None and new_file_content is None:
        return None
    
    # safe_file_path = file_path.replace('/', '_')
    # file_name = f"{prefix}_{safe_file_path}"
    # full_path = os.path.join(directory, file_name)

    # with open(full_path, 'w') as file:
    #     file.write(file_content)
    
    return old_file_content, new_file_content

def main(commit_hash, output_directory, output_file):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    changed_files = get_changed_files(commit_hash)
    for file_path in changed_files:
        # Save the file content before the commit
        parent_commit = f"{commit_hash}^"
        # before_file_path = save_file_content(parent_commit, file_path, output_directory, "before")
        # if before_file_path:
        #     print(f"Saved before version of {file_path} to {before_file_path}")
        
        # Save the file content after the commit
        # after_file_path = save_file_content(commit_hash, file_path, output_directory, "after")
        # if after_file_path:
        #     print(f"Saved after version of {file_path} to {after_file_path}")

if __name__ == "__main__":
    # if len(sys.argv) != 3:
    #     print("Usage: python script.py <commit_hash> <output_directory>")
    #     sys.exit(1)
    # commit_hash = sys.argv[1]
    # output_directory = sys.argv[2]

    path = "/Users/mac/Desktop/Java"
    os.chdir(path)

    commit_hash = "05ca93eace893a75e886a19739778a67bd3a18bc"
    output = "/Users/mac/Desktop/TestEvolution/output"
    # main(commit_hash, output)
    changed_files = get_changed_files(commit_hash)
    print(changed_files)
