# +---------------------------------------------------------------------+
# | Modified from AnWen <https://github.com/anwen-anyi>                 |
# +---------------------------------------------------------------------+
# | For the unmodified version you can ask in <https://t.me/alist_chat> |
# +---------------------------------------------------------------------+

import requests
import os
import time
import mysql.connector
import re


# owner = os.environ["owner"]
# repo = os.environ["repo"]
# tag_name = os.environ["tag_name"]
# access_token = os.environ["PAT"]
# proxy_url = os.environ["proxy_url"]
# alist_folder = os.environ["alist_folder"]
# mysql_user = os.environ["mysql_user"]
# mysql_password = os.environ["mysql_password"]
# mysql_host = os.environ["mysql_host"]
# mysql_database = os.environ["mysql_database"]
# storage_id = os.environ["storage_id"]
# site_url = os.environ["site_url"]
# username = os.environ["username"]
# password = os.environ["password"]
# referer = os.environ["referer"]

# 登录 API
def login(username, password, site_url, referer):
    url = "https://" + site_url + "/api/auth/login"
    headers = {
        "Referer": referer
    }
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(url, headers=headers, json=data, verify=False)
    if response.status_code == 200:
        try:
            token = response.json()["data"]["token"]
            return token
        except ValueError:
            print("响应内容不是 JSON 格式")
            return None
    else:
        print("登录失败，状态码：", response.status_code)
        return None


# 禁用存储 API
def disable_storage(token, storage_id, site_url, referer):
    url = "https://" + site_url + "/api/admin/storage/disable"
    headers = {
        "Authorization": token,
        "Referer": referer
    }
    params = {
        "id": storage_id
    }
    response = requests.post(url, headers=headers, params=params, verify=False)
    if response.status_code == 200:
        return True
    else:
        return False


# 启用存储 API
def enable_storage(token, storage_id, site_url, referer):
    url = "https://" + site_url + "/api/admin/storage/enable"
    headers = {
        "Authorization": token,
        "Referer": referer
    }
    params = {
        "id": storage_id
    }
    response = requests.post(url, headers=headers, params=params, verify=False)
    if response.status_code == 200:
        return True
    else:
        return False


# Replace with your own values
owner = os.environ["owner"]
repo = os.environ["repo"]
tag_name = os.environ["tag_name"]
access_token = os.environ["PAT"]
proxy_url = os.environ["proxy_url"]  # Leave empty if no proxy is needed
proxies = {'http': proxy_url, 'https': proxy_url} if proxy_url else None

# Get the release information
if tag_name:
    url = f'https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag_name}'
else:
    url = f'https://api.github.com/repos/{owner}/{repo}/releases/latest'
headers = {'Authorization': f'token {access_token}'}
response = requests.get(url, headers=headers)
release_info = response.json()

# Write the download links to a text file
alist_folder = os.environ["alist_folder"]
filename = "github_releases_" + tag_name + ".txt"
# if tag_name:
#     filename = github_releases_{tag_name}.txt'
# else:
#     filename = 'github_releases_latest.txt'
with open(filename, 'w') as f:
    f.write(alist_folder + ":" + r"\n")
    for asset in release_info['assets']:
        download_url = asset['browser_download_url']
        file_name = os.path.basename(download_url)
        file_size = asset['size']
        if proxies:
            download_url = f'{proxy_url}/{download_url}'
        file_time_original = asset['updated_at']
        file_time_original_array = time.strptime(file_time_original, "%Y-%m-%dT%H:%M:%SZ")
        file_time = int(time.mktime(file_time_original_array))
        # unix_time = int(time.time())
        formatted_link = f'{file_name}:{file_size}:{file_time}:{download_url}'
        f.write(" " + " " + formatted_link + r"\n")

# 建立数据库连接
storage_id = os.environ["storage_id"]
mysql_user = os.environ["mysql_user"]
mysql_password = os.environ["mysql_password"]
mysql_host = os.environ["mysql_host"]
mysql_database = os.environ["mysql_database"]
cnx = mysql.connector.connect(user=mysql_user, password=mysql_password,
                              host=mysql_host, database=mysql_database)

# 获取游标
cursor = cnx.cursor()

# 将之前数据库中的数据写入文件
alist_early_txt = "github_releases_alist_early.txt"
with open(alist_early_txt, 'w') as f:
    addition_sql = "SELECT addition FROM x_storages WHERE id = " + storage_id
    cursor.execute(addition_sql)
    addition_rows = cursor.fetchall()
    addition = str(addition_rows)
    addition_match = re.search(r'(?<=\{"url_structure":").*?(?=",\"head_size":false\})', addition)
    f.write(addition_match.group())

# 读取txt文件
with open(alist_early_txt, "r") as f:
    content = f.read()

# 将\\n替换为\n
content = content.replace(r"\\n", r"\n")

# 写入新的txt文件
with open(alist_early_txt, "w") as f:
    f.write(content)


# 合并TXT
def merge_txt(files):
    with open('github_releases_alist.txt', 'w') as f:
        for file in files:
            with open(file, 'r') as t:
                for line in t:
                    f.write(line)


files = [filename, alist_early_txt]
merge_txt(files)

# 读取文本文件
with open("github_releases_alist.txt", 'r') as f:
    lines = f.read()
    # 去除每行结尾的换行符
    # lines = [line.rstrip('\n') for line in lines]
    # # 判断最后一行是否有换行符
    # if not lines[-1].endswith('\n'):
    #     last_line = lines[-1]
    #     lines = lines[:-1]
    # else:
    #     last_line = lines.pop()
    # # 将最后一行加回到 lines 列表中
    # lines.append(last_line)

# 更新数据库中的 addition 列
addition = '{"url_structure": "' + str(lines) + '","head_size":false}'
query = "UPDATE x_storages SET addition = %s WHERE id = " + storage_id
values = (addition,)
cursor.execute(query, values)
cnx.commit()

# 关闭游标和连接
cursor.close()
cnx.close()

# 登录
site_url = os.environ["site_url"]
username = os.environ["username"]
password = os.environ["password"]
referer = os.environ["referer"]
token = login(username, password, site_url, referer)
if token is None:
    print("登录失败")
    exit()

# 禁用存储
# storage_id = os.environ["storage_id"]
if disable_storage(token, storage_id, site_url, referer):
    print("禁用存储成功")
    time.sleep(10)  # 停止 10 秒钟
else:
    print("禁用存储失败")
    exit()

# 启用存储
if enable_storage(token, storage_id, site_url, referer):
    print("启用存储成功")
else:
    print("启用存储失败")
    exit()
