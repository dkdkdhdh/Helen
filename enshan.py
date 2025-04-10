#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -------------------------------
# 原作者@Author : github@wd210010 
# @Time : 2023/10/4 16:23
# -------------------------------
# cron "0 0 2 * * *" script-path=enshan_sign.py,tag=恩山签到
# 使用WxPusher推送需配置两个环境变量：
# 1. WXPUSHER_APP_TOKEN (从wxpusher.zjiecode.com获取)
# 2. WXPUSHER_TOPIC_IDS (消息接收主题ID)
#使用DEEPSEEK修改，青龙脚本自用@Author:Lilithoffice365

"""
cron：40 0,0 * * *
const $ = new Env('恩山无线论坛签到')
"""

import requests
import re
import os

# ------------------- 配置区 -------------------
# 从环境变量读取配置
ENSHAN_COOKIE = os.getenv("enshanck")      # 恩山Cookie
WXPUSHER_TOKEN = os.getenv("WXPUSHER_APP_TOKEN")  # WxPusher的AppToken
TOPIC_ID = os.getenv("WXPUSHER_TOPIC_IDS")  # 消息接收主题ID(纯数字)

# ------------------- 推送函数 -------------------
def wxpusher_push(content):
    """
    使用WxPusher发送消息
    参数：content (要推送的字符串内容)
    """
    if not all([WXPUSHER_TOKEN, TOPIC_ID]):
        print("推送失败：未配置WxPusher参数！")
        return

    api_url = "https://wxpusher.zjiecode.com/api/send/message"
    headers = {'Content-Type': 'application/json'}
    
    # 注意：topicIds必须是整数列表格式
    payload = {
        "appToken": WXPUSHER_TOKEN,
        "content": content.replace('\n', '<br>'),
        "topicIds": [int(TOPIC_ID)],  # 转换为整数列表
        "contentType": 2,             # 2表示HTML格式
        "verifyPay": False            # 不需要付费验证
    }

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
        result = resp.json()
        if result.get("code") == 1000:
            print("✅ WxPusher推送成功")
        else:
            print(f"推送失败：{result.get('msg')}")
    except Exception as e:
        print(f"推送请求异常：{str(e)}")

# ------------------- 主逻辑 -------------------
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36",
    "Cookie": ENSHAN_COOKIE,
}

session = requests.Session()
try:
    # 获取账户信息
    response = session.get(
        'https://www.right.com.cn/FORUM/home.php?mod=spacecp&ac=credit&showcredit=1',
        headers=headers,
        timeout=10
    )
    response.raise_for_status()
    
    # 提取数据
    coin = re.findall("恩山币: </em>(.*?)&nbsp;", response.text)[0]
    point = re.findall("<em>积分: </em>(.*?)<span", response.text)[0]
    
    # 格式化消息
    message = (
        "🏷️ 恩山无线论坛签到\n"
        f"💰 恩山币：{coin}\n"
        f"📊 积分：{point}\n"
        "⏰ 数据更新时间：每日01:05左右"
    )
    
    print(message)
    wxpusher_push(message)

except IndexError:
    print("错误：网页数据解析失败，请检查Cookie有效性")
except requests.exceptions.RequestException as e:
    print(f"网络请求失败：{str(e)}")
except Exception as e:
    print(f"未知错误：{str(e)}")
