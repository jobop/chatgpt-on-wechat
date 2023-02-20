# encoding:utf-8




"""
wechat common channel
"""
import werobot
from werobot.replies import ArticlesReply, Article
import json

from channel.channel import Channel
from concurrent.futures import ThreadPoolExecutor
from common.log import logger
from config import conf
from pybloom_live import BloomFilter

import requests
import io
import time

thread_pool = ThreadPoolExecutor(max_workers=8)
robot = werobot.WeRoBot(token='QRHotP7IE94bMdCZYLvWo1N0trkThe')
bloom = BloomFilter(capacity=1000, error_rate=0.001)

@robot.text
@robot.voice
def handler_text_msg(msg,session):
    # openid+shi时间戳放布隆过滤器，存在则直接返回
    if msg.type == "text":
        logger.info("[WX]########receive msg: " + msg.content)
    elif msg.type == "voice":
        logger.info("[WX]########receive msg: " + msg.recognition)

    from_user_id = msg.source
    if msg.type == "text":
        content = msg.content
    elif msg.type == "voice":
        content= msg.recognition
    else:
        content = msg.content

    channel = WechatCommonChannel()

    send_time = msg.time
    # 因为session本来就是以用户纬度隔离的，所以这里以消息时间作为key就可以
    msgKey = str(send_time)

    resp , need = need_continue(session,msgKey,msgKey+"@count")
    if not need:
        logger.info("[WX]########resp msg from cache: " + resp)
        render(msg,content,channel,resp,from_user_id)
        return resp


    reply_text = channel.handle(msg)
    # wx会5秒内不返回则重试，重试3次，这样会导致程序每次都重新处理，而且还处理不完，这里把key和应答存session中，有则直接返回，没有就往下走，这样可以延长思考时间
    session[msgKey] = reply_text
    logger.info("[WX]########resp msg from openai: " + reply_text)
    return render(msg,content,channel,reply_text,from_user_id)

def render(msg,query,channel,reply_text,from_user_id):
    img_match_prefix = channel.check_prefix(query, conf().get('image_create_prefix'))
    if img_match_prefix:
        reply = ArticlesReply(message=msg)
        article = Article(
                    title="这个画得满意吗？",
                    description=query,
                    img=reply_text,
                    url=reply_text
                )
        reply.add_article(article)
        return reply
    else:
        return reply_text


def need_continue(session,msgKey,msgCountKey):
    req_count_str = session.get(msgCountKey)
    if not req_count_str:
        req_count=0
    else:
        req_count=int(req_count_str)
    req_count=req_count + 1
    session[msgKey+"@count"]=str(req_count)

    #微信第一次请求，直接让它去请求openai
    if req_count == 1:
        return "", True
    else:
        #先判断下有就返回
        if session[msgKey]:
            return session[msgKey], False
        # pin 3次，每次2s
        pin=3
        while not session[msgKey] and pin>0:
            time.sleep(2)
            pin = pin-1

        return session[msgKey] , False

    #
    # last_reply = session.get(msgKey)
    # if not last_reply:
    #     session[msgKey] = "%%$$###"
    #     return "" , True
    #
    # if last_reply == "%%$$###":
    #
    # else:
    #     return session[msgKey], False


class WechatCommonChannel(Channel):
    def __init__(self):
        pass

    def startup(self):
        robot.config['HOST'] = '0.0.0.0'
        robot.config['PORT'] = 8889
        robot.run(server='tornado')
        robot.run()

    def handle(self, msg):
        try:
            from_user_id = msg.source
            if msg.type == "text":
                content = msg.content
            elif msg.type == "voice":
                content= msg.recognition
            else:
                content = msg.content

            # thread_pool.submit(self._do_send, content, from_user_id)
            return self._do_send(content,from_user_id)
        except Exception as e:
            logger.exception(e)
            return "系统开小差了"

    def send(self, msg, receiver):
        logger.debug('[WX] sendMsg={}, receiver={}'.format(msg, receiver))
        return msg
    def check_prefix(self, content, prefix_list):
        for prefix in prefix_list:
            if content.startswith(prefix):
                return prefix
        return None
    def _do_send(self, query, reply_user_id):
        try:
            if not query:
                return
            context = dict()
            context['from_user_id'] = reply_user_id
            context['type'] = 'TEXT'
            img_match_prefix = self.check_prefix(query, conf().get('image_create_prefix'))
            if img_match_prefix:
                context['type'] = 'IMAGE_CREATE'
            reply_text = super().build_reply_content(query, context)
            if reply_text:
                return reply_text

        except Exception as e:
            logger.exception(e)
            return "系统开小差了"

