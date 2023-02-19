# encoding:utf-8




"""
wechat common channel
"""
import werobot
import itchat
import json
from itchat.content import *
from channel.channel import Channel
from concurrent.futures import ThreadPoolExecutor
from common.log import logger
from config import conf
import requests
import io

thread_pool = ThreadPoolExecutor(max_workers=8)
robot = werobot.WeRoBot(token='QRHotP7IE94bMdCZYLvWo1N0trkThe')

@robot.text
def handler_single_msg(msg):
    WechatCommonChannel().handle(msg)
    return None


@itchat.msg_register(TEXT, isGroupChat=True)
def handler_text_msg(msg):
    WechatCommonChannel().handle(msg)
    return None


class WechatCommonChannel(Channel):
    def __init__(self):
        pass

    def startup(self):
        robot.run()

    def handle(self, msg):
        logger.debug("[WX]receive msg: " + json.dumps(msg, ensure_ascii=False))
        from_user_id = msg['FromUserName']
        content = msg['Text']
        thread_pool.submit(self._do_send, content, from_user_id)

    def send(self, msg, receiver):
        logger.info('[WX] sendMsg={}, receiver={}'.format(msg, receiver))
        itchat.send(msg, toUserName=receiver)
        robot.text()

    def _do_send(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['from_user_id'] = reply_user_id
            reply_text = super().build_reply_content(query, context)
            if reply_text:
                self.send(conf().get("single_chat_reply_prefix") + reply_text, reply_user_id)
        except Exception as e:
            logger.exception(e)

