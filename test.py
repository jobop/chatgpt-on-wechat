from bridge.bridge import Bridge
import config
if __name__ == '__main__':
    config.load_config()
    context = dict()
    context['type'] = 'TEXT'
    context['from_user_id'] ='zhengwei'
    print(Bridge().fetch_reply_content("你是一个机器人吗", context))