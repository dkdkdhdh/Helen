#!/usr/bin/python3
# -- coding: utf-8 --
# @Time : 2023/4/8 10:23
# -------------------------------
# cron "30 5 * * *" script-path=xxx.py,tag=匹配cron用
# const $ = new Env('阿里云盘签到');
"""
cron：30 0,0 * * *
const $ = new Env('阿里云盘签到')
"""

import json
import requests
import os

##变量export ali_refresh_token=''
ali_refresh_token = os.getenv("ali_refresh_token").split('&')
# refresh_token是一成不变的呢，我们使用它来更新签到需要的access_token
# refresh_token获取教程：https://github.com/bighammer-link/Common-scripts/wiki/%E9%98%BF%E9%87%8C%E4%BA%91%E7%9B%98refresh_token%E8%8E%B7%E5%8F%96%E6%96%B9%E6%B3%95

# WxPusher配置
WXPUSHER_TOKEN = os.getenv("WXPUSHER_APP_TOKEN")  # WxPusher的AppToken
TOPIC_IDS = os.getenv("WXPUSHER_TOPIC_IDS")      # 消息接收主题ID（多个用逗号分隔）

# WxPusher推送函数
def wxpusher_send(content):
    if not WXPUSHER_TOKEN or not TOPIC_IDS:
        print("WxPusher配置不完整，无法发送消息")
        return
    url = f"https://wxpusher.zjiecode.com/api/send/message"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "appToken": WXPUSHER_TOKEN,
        "content": content,
        "topicIds": [int(tid) for tid in TOPIC_IDS.split(",")],
        "summary": "阿里云盘签到结果"
    }
    response = requests.post(url=url, headers=headers, data=json.dumps(data), verify=False)
    if response.status_code == 200:
        print("消息推送成功")
    else:
        print(f"消息推送失败，错误信息：{response.text}")

# 签到函数
def daily_check(access_token):
    url = 'https://member.aliyundrive.com/v1/activity/sign_in_list'
    headers = {
        'Authorization': access_token,
        'Content-Type': 'application/json'
    }
    response = requests.post(url=url, headers=headers, json={}).text
    result = json.loads(response)
    sign_days = result['result']['signInCount']
    data = {
        'signInDay': sign_days
    }
    url_reward = 'https://member.aliyundrive.com/v1/activity/sign_in_reward'
    resp2 = requests.post(url=url_reward, headers=headers, data=json.dumps(data))
    result2 = json.loads(resp2.text)
    if 'success' in result:
        print('签到成功')
        for i, j in enumerate(result['result']['signInLogs']):
            if j['status'] == 'miss':
                day_json = result['result']['signInLogs'][i - 1]
                if not day_json['isReward']:
                    content = '签到成功，今日未获得奖励'
                else:
                    content = '本月累计签到{}天，今日签到获得{}{}'.format(result['result']['signInCount'],
                                                                         day_json['reward']['name'],
                                                                         day_json['reward']['description'])
                print(content)
                return content

# 使用refresh_token更新access_token
def update_token(refresh_token):
    url = 'https://auth.aliyundrive.com/v2/account/token'
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    response = requests.post(url=url, json=data).json()
    access_token = response['access_token']
    return access_token

# 主函数
def main():
    for i in range(len(ali_refresh_token)):
        print(f'🚀 开始账号{i + 1}签到')
        access_token = update_token(ali_refresh_token[i])
        content = daily_check(access_token)
        if content:
            wxpusher_send(content)

if __name__ == '__main__':
    main()
