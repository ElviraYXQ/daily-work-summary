#!/usr/bin/env python3
import requests
import os

app_id = "cli_a9418088f5b8dcb1"
app_secret = "EOWnlL3vjmmoE0rqshYpmfk2UjGPmd42"

# 获取token
url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
token = resp.json().get("tenant_access_token")

# 通过user_id获取open_id
url2 = "https://open.feishu.cn/open-apis/contact/v3/users/ou_cc38ac881bcf17d997f0cad7d9a9a621"
headers = {"Authorization": f"Bearer {token}"}
resp2 = requests.get(url2, headers=headers)
print(resp2.json())
