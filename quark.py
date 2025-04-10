#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -------------------------------
# @Author : github@wd210010 
# @Time : 2024/5/4 16:23
# -------------------------------
# cron "0 0 2 * * *" script-path=quark_sign.py,tag=夸克签到
# 使用WxPusher推送需配置两个环境变量：
# 1. WXPUSHER_APP_TOKEN (从wxpusher.zjiecode.com获取)
# 2. WXPUSHER_TOPIC_IDS (消息接收主题ID)
#使用DEEPSEEK修改，青龙脚本自用@Author:Lilithoffice365
import os
import re
import sys
import requests

# ------------------- 配置区 -------------------
# 从环境变量读取配置
WXPUSHER_TOKEN = os.getenv("WXPUSHER_APP_TOKEN")  # WxPusher的AppToken
TOPIC_IDS = os.getenv("WXPUSHER_TOPIC_IDS")      # 消息接收主题ID（多个用逗号分隔）

# ------------------- 推送函数 -------------------
def wxpusher_push(content):
    """
    使用WxPusher发送消息
    参数：content (要推送的字符串内容)
    """
    if not all([WXPUSHER_TOKEN, TOPIC_IDS]):
        print("推送失败：未配置WxPusher参数！")
        return

    api_url = "https://wxpusher.zjiecode.com/api/send/message"
    headers = {'Content-Type': 'application/json'}
    
    # 注意：topicIds必须是整数列表格式
    topic_ids = [int(topic_id.strip()) for topic_id in TOPIC_IDS.split(",")]
    
    payload = {
        "appToken": WXPUSHER_TOKEN,
        "content": content.replace('\n', '<br>'),
        "topicIds": topic_ids,  # 转换为整数列表
        "contentType": 2,       # 2表示HTML格式
        "verifyPay": False      # 不需要付费验证
    }

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
        result = resp.json()
        if result.get("code") == 1000:
            print("✅ WxPusher推送成功；推送02:05:05左右")
        else:
            print(f"推送失败：{result.get('msg')}")
    except Exception as e:
        print(f"推送请求异常：{str(e)}")

# ------------------- 获取环境变量 -------------------
def get_env():
    # 判断 COOKIE_QUARK是否存在于环境变量
    if "COOKIE_QUARK" in os.environ:
        # 读取系统变量以 \n 或 && 分割变量
        cookie_list = re.split('\n|&&', os.environ.get('COOKIE_QUARK'))
    else:
        # 标准日志输出
        print('❌未添加COOKIE_QUARK变量')
        sys.exit(0)

    return cookie_list

# ------------------- 夸克签到类 -------------------
class Quark:
    def __init__(self, cookie):
        self.cookie = cookie

    def get_growth_info(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
        querystring = {"pr": "ucpro", "fr": "pc", "uc_param_str": ""}
        headers = {
            "content-type": "application/json",
            "cookie": self.cookie
        }
        response = requests.get(url=url, headers=headers, params=querystring).json()
        if response.get("data"):
            return response["data"]
        else:
            return False

    def get_growth_sign(self):
        url = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
        querystring = {"pr": "ucpro", "fr": "pc", "uc_param_str": ""}
        payload = {"sign_cyclic": True}
        headers = {
            "content-type": "application/json",
            "cookie": self.cookie
        }
        response = requests.post(url=url, json=payload, headers=headers, params=querystring).json()
        if response.get("data"):
            return True, response["data"]["sign_daily_reward"]
        else:
            return False, response["message"]

    def get_account_info(self):
        url = "https://pan.quark.cn/account/info"
        querystring = {"fr": "pc", "platform": "pc"}
        headers = {
            "content-type": "application/json",
            "cookie": self.cookie
        }
        response = requests.get(url=url, headers=headers, params=querystring).json()
        if response.get("data"):
            return response["data"]
        else:
            return False

    def do_sign(self):
        msg = ""
        # 验证账号
        account_info = self.get_account_info()
        if not account_info:
            msg = f"\n❌该账号登录失败，cookie无效"
        else:
            log = f" 昵称: {account_info['nickname']}"
            msg += log + "\n"
            # 每日领空间
            growth_info = self.get_growth_info()
            if growth_info:
                if growth_info["cap_sign"]["sign_daily"]:
                    log = f"✅ 执行签到: 今日已签到+{int(growth_info['cap_sign']['sign_daily_reward'] / 1024 / 1024)}MB，连签进度({growth_info['cap_sign']['sign_progress']}/{growth_info['cap_sign']['sign_target']})"
                    msg += log + "\n"
                else:
                    sign, sign_return = self.get_growth_sign()
                    if sign:
                        log = f"✅ 执行签到: 今日签到+{int(sign_return / 1024 / 1024)}MB，连签进度({growth_info['cap_sign']['sign_progress'] + 1}/{growth_info['cap_sign']['sign_target']})"
                        msg += log + "\n"
                    else:
                        msg += f"✅ 执行签到: {sign_return}\n"

        return msg

# ------------------- 主函数 -------------------
def main():
    msg = ""
    global cookie_quark
    
    cookie_quark = get_env()

    print("✅检测到共", len(cookie_quark), "个夸克账号\n")

    i = 0
    while i < len(cookie_quark):
        # 开始任务
        log = f"🙍🏻‍♂️ 第{i + 1}个账号"
        msg += log
        # 登录
        log = Quark(cookie_quark[i]).do_sign()
        msg += log + "\n"

        i += 1

    print(msg)
    wxpusher_push(msg)  # 推送结果

    return msg[:-1]

# ------------------- 脚本入口 -------------------
if __name__ == "__main__":
    print("----------夸克网盘开始尝试签到----------")
    main()
    print("----------夸克网盘签到执行完毕----------")