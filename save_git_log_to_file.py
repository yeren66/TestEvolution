import subprocess
import os

def save_git_log_to_file(repo_path, file_path):
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
            print(f"Error: {stderr.decode('utf-8')}")
            return

    finally:
        # 无论如何都回到原来的目录
        os.chdir(original_path)

    # 在原来的目录中写入输出
    with open(file_path, "w") as file:
        file.write(stdout.decode("utf-8"))

    return stdout.decode('utf-8')

if __name__ == "__main__":

    # Java项目的路径
    java_project_path = "/home/yeren/java-project/commons-math"  # omen
    # java_project_path = "/Users/mac/Desktop/Java"  # mac

    # 输出文件的路径
    output_file_path = "git_log.txt"

    # 调用函数
    log_text = save_git_log_to_file(java_project_path, output_file_path)
