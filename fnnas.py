"""
cron:50 0,0 * * *
const $ = new Env('飞牛论坛签到')
"""

import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

pvRK_2132_saltkey = os.getenv('fn_pvRK_2132_saltkey')
pvRK_2132_auth = os.getenv('fn_pvRK_2132_auth')
pvRK_2132_sign = os.getenv('fn_pvRK_2132_sign')

PUSH_PLUS_TOKEN = ''  # push+ 微信推送的用户令牌
# server 酱的 PUSH_KEY，兼容旧版与 Turbo 版
PUSH_KEY = ''
if os.getenv('PUSH_PLUS_TOKEN'):
    PUSH_PLUS_TOKEN = os.getenv('PUSH_PLUS_TOKEN')
if os.getenv('PUSH_KEY'):
    PUSH_KEY = os.getenv('PUSH_KEY')


# 填写对应的 Cookie 值
cookies = {
    'pvRK_2132_saltkey': pvRK_2132_saltkey,
    'pvRK_2132_auth': pvRK_2132_auth,
}
# SMTP 邮件服务配置
push_config = {
    'SMTP_SERVER': '',  # SMTP 发送邮件服务器，形如 smtp.exmail.qq.com:465
    'SMTP_SSL': 'true',  # SMTP 发送邮件服务器是否使用 SSL，填写 true 或 false
    'SMTP_EMAIL': '',  # SMTP 收发件邮箱，通知将会由自己发给自己
    'SMTP_PASSWORD': '',  # SMTP 登录密码，也可能为特殊口令，视具体邮件服务商说明而定
    'SMTP_NAME': '定时任务',  # SMTP 收发件人姓名，可随意填写
}

def sign_in():
    try:
        # 签到请求链接右键打卡按钮直接复制替换
        # response = requests.get('**签到请求链接右键打卡按钮直接复制替换**', cookies=cookies)
        response = requests.get('https://club.fnnas.com/plugin.php?id=zqlj_sign&sign='+pvRK_2132_sign, cookies=cookies)

        if '恭喜您，打卡成功！' in response.text:
            print('签到详情（打卡成功）：\n')
            get_sign_in_info()
        elif '您今天已经打过卡了，请勿重复操作！' in response.text:
            print('签到详情（已经打过卡了）：\n')
            get_sign_in_info()
        else:
            print('打卡失败, cookies可能已经过期或站点更新.')
            smtp(title='飞牛社区自动签到(打卡失败)', content='cookies可能已经过期或站点更新.')  # 发送邮件
    except Exception as error:
        print('签到请求失败:', error)
        smtp(title='飞牛社区自动签到(请求失败)', content=str(error))  # 发送邮件


def get_sign_in_info():
    try:
        response = requests.get('https://club.fnnas.com/plugin.php?id=zqlj_sign', cookies=cookies)

        soup = BeautifulSoup(response.text, 'html.parser')
        content = []

        # 定义需要查找的模式和选择器
        patterns = [
            {'name': '最近打卡', 'selector': 'li:-soup-contains("最近打卡")'},
            {'name': '本月打卡', 'selector': 'li:-soup-contains("本月打卡")'},
            {'name': '连续打卡', 'selector': 'li:-soup-contains("连续打卡")'},
            {'name': '累计打卡', 'selector': 'li:-soup-contains("累计打卡")'},
            {'name': '累计奖励', 'selector': 'li:-soup-contains("累计奖励")'},
            {'name': '最近奖励', 'selector': 'li:-soup-contains("最近奖励")'},
            {'name': '当前打卡等级', 'selector': 'li:-soup-contains("当前打卡等级")'}
        ]

        for pattern in patterns:
            element = soup.select_one(pattern['selector'])
            if element:
                # 提取文本并清洗
                text = element.get_text()
                content.append(f"{pattern['name']}: {text.split('：')[-1].strip()}")
        content_text = '\n'.join(content)
        print(content_text + '\n')
        xxts(title='飞牛社区自动签到(成功)', content=str(content_text))  # 消息推送
        smtp(title='飞牛社区自动签到(成功)', content=str(content_text))  # 发送邮件

    except Exception as error:
        print('获取打卡信息失败:', error)
        xxts(title='飞牛社区自动签到(获取打卡信息失败)', content=str(error))  # 消息推送
        smtp(title='飞牛社区自动签到(获取打卡信息失败)', content=str(error))  # 发送邮件

def post_msg(url: str, data: dict) -> bool:
    response = requests.post(url, data=data)
    code = response.status_code
    if code == 200:
        return True
    else:
        return False

def PushPlus_send(token, title: str, desp: str = '', template: str = 'markdown') -> bool:
    url = 'http://www.pushplus.plus/send'
    data = {
        'token': token,  # 用户令牌
        'title': title,  # 消息标题
        'content': desp,  # 具体消息内容，根据不同template支持不同格式
        'template': template,  # 发送消息模板
    }
    return post_msg(url, data)


def ServerChan_send(sendkey, title: str, desp: str = '') -> bool:
    url = 'https://sctapi.ftqq.com/{0}.send'.format(sendkey)
    data = {
        'title': title,  # 消息标题，必填。最大长度为 32
        'desp': desp  # 消息内容，选填。支持 Markdown语法 ，最大长度为 32KB ,消息卡片截取前 30 显示
    }
    return post_msg(url, data)

def xxts(title: str, content: str):
    msg = title + '\n\n' + content
    if PUSH_KEY:
        ServerChan_send(PUSH_KEY, title, msg)
        print("PUSH_KEY推送成功")
    if PUSH_PLUS_TOKEN:
        PushPlus_send(PUSH_PLUS_TOKEN, title, msg)
        print("PUSH_PLUS_TOKEN推送成功")

def smtp(title: str, content: str):
    """
    使用 SMTP 邮件 推送消息。
    """
    if (
            not push_config.get("SMTP_SERVER")
            or not push_config.get("SMTP_SSL")
            or not push_config.get("SMTP_EMAIL")
            or not push_config.get("SMTP_PASSWORD")
            or not push_config.get("SMTP_NAME")
    ):
        print("SMTP 邮件 的 SMTP_SERVER 或者 SMTP_SSL 或者 SMTP_EMAIL 或者 SMTP_PASSWORD 或者 SMTP_NAME 未设置!!\n取消邮箱推送")
        return
    print("SMTP 邮件 服务启动")

    message = MIMEText(content, "plain", "utf-8")
    message["From"] = formataddr(
        (
            Header(push_config.get("SMTP_NAME"), "utf-8").encode(),
            push_config.get("SMTP_EMAIL"),
        )
    )
    message["To"] = formataddr(
        (
            Header(push_config.get("SMTP_NAME"), "utf-8").encode(),
            push_config.get("SMTP_EMAIL"),
        )
    )
    message["Subject"] = Header(title, "utf-8")

    try:
        smtp_server = (
            smtplib.SMTP_SSL(push_config.get("SMTP_SERVER"))
            if push_config.get("SMTP_SSL") == "true"
            else smtplib.SMTP(push_config.get("SMTP_SERVER"))
        )
        smtp_server.login(
            push_config.get("SMTP_EMAIL"), push_config.get("SMTP_PASSWORD")
        )
        smtp_server.sendmail(
            push_config.get("SMTP_EMAIL"),
            push_config.get("SMTP_EMAIL"),
            message.as_bytes(),
        )
        smtp_server.close()
        print("SMTP 邮件 推送成功！")
    except Exception as e:
        print(f"SMTP 邮件 推送失败！{e}")


if __name__ == '__main__':
    sign_in()
