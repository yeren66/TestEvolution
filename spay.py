import requests
import json
import re
from tqdm import tqdm

headers = {'User-Agent':'Mozilla/5.0',
        'Authorization': 'token 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',
        'Content-Type':'application/json',
        'Accept':'application/json'
        }

def save_to_file(content, filename="result.json"):
    with open(filename, "w") as f:
        f.write(json.dumps(content, indent=4))

def get_java_repositories_with_stars(page=1):
    url = "https://api.github.com/search/repositories"
    params = {
        "q": "language:java stars:>10",
        "sort": "stars",
        "order": "desc",
        "page": page,
        "per_page": "100"
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()["items"]
    else:
        print("Error: Failed to fetch repositories")
        return []
    
def get_commit_count_with_regex(url):
    try:
        # 发送 GET 请求到 URL
        response = requests.get(url)
        # 检查响应是否成功
        if response.status_code == 200:
            # 使用正则表达式查找提交计数
            match = re.search(r'"commitCount":"([\d,]+)"', response.text)
            if match:
                # Extract the commit count and remove commas
                commit_count = match.group(1).replace(',', '')
                commit_count_number = int(commit_count)
            else:
                commit_count_number = "Commit count not found in the file."
            return commit_count_number
        else:
            return f"无法从 URL 获取响应，状态码: {response.status_code}"
    except Exception as e:
        return f"发生错误: {e}"

def size_filter(repo):
    if repo["size"] > 1000 and repo["size"] < 1000000:
        return True
    return False

def commit_count_filter(repo):
    url = repo['html_url']
    commit_count = get_commit_count_with_regex(url)
    if type(commit_count) == int and commit_count >= 500:
        return True
    return False

def has_pom_file_filter(repo):
    url = repo["contents_url"].replace("{+path}", "")
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        files = response.json()
        for file in files:
            if file["name"] == "pom.xml":
                return True
    return False

# def filter_pom_file(url):
#     response = requests.get(url, headers=headers)
#     txt = ""
#     if response.status_code == 200:
#         txt = response.text
#     pattern = r'junit'
#     match = re.search(pattern, txt)
#     if match:
#         return True
#     return False



if __name__ == "__main__":
    repositories = []
    for page in tqdm(range(1, 50)):
        repositories.extend(get_java_repositories_with_stars(page))
    filtered_repositories = list(filter(commit_count_filter, repositories))
    filtered_repositories = list(filter(has_pom_file_filter, filtered_repositories))
    print("Total repositories:", len(repositories))
    print("Filtered repositories:", len(filtered_repositories))
    # save_to_file(filtered_repositories)
    # result = []
    # for repo in tqdm(filtered_repositories):
    #     try:
    #         url = has_pom_file(repo)
    #         if url:
    #             # if filter_pom_file(url):
    #             result.append(repo['html_url'])
    #     except:
    #         continue
    # save_to_file(result, "result1.json")
    save_to_file(filtered_repositories, "result1.json")