#!/usr/bin/env python
# coding: utf-8

import Queue
from datetime import datetime, timedelta
from wxbot import *


class XiaoBingWXBot(WXBot):
    def __init__(self):
        WXBot.__init__(self)

        # === 配置信息 start ===
        self.robot_name = u'小冰'          # 代理聊天机器人名称
        self.watch_gname = u'智能测试'      # 监听群名称，只有监听的群才会处理，暂只支持一个群的监听
        self.cur_chat_timeout_second = 10  # 每次会话等待时间，超过自动切换其他人

        self.in_chat_tip_msg = u'你好，超哥有事不在。我是他的机器人助理，我上知天文，下知地理，欢迎与我聊天~'    # 机器人进入聊天提示
        # === 配置信息 end ===

        self.robot_switch = True            # 机器人天关
        self.wait_robot_dtime = datetime.today() - timedelta(days=1)        # 最后一次等待机器人回复时间，回复完成自动清空
        self.cur_chat_type = None           # 当前聊天类型： 3、 群消息； 4、 联系人；
        self.robot_uid = None               # 代理聊天机器人ID
        self.watch_gid = None               # 监听群ID
        self.cur_chat_uid = None            # 当前聊天人ID

        self.cur_chat_last_time = datetime.today() - timedelta(days=1)      # 与当前聊天人最后一次聊天时间
        self.need_chat_queue = Queue.Queue()    # 待聊天队列，包含监听的群信息，与联系人信息

    def auto_switch(self, msg):
        msg_data = msg['content']['data']
        stop_cmd = [u'退下', u'走开', u'关闭', u'关掉', u'休息', u'滚开']
        start_cmd = [u'出来', u'启动', u'工作', u'开启']

        watch_gname_action = 'watch ', msg_data
        for account in self.group_list:
            if watch_gname_action == account['NickName']:
                self.watch_gname = account['NickName']
                self.watch_gid = account['UserName']
                print '    swith watch group:', account['NickName'], self.watch_gid
                return

        if self.robot_switch:
            for i in stop_cmd:
                if i == msg_data:
                    self.robot_switch = False
                    self.send_msg_by_uid(u'[Robot]' + u'机器人已关闭！', msg['to_user_id'])
                    return
        else:
            for i in start_cmd:
                if i == msg_data:
                    self.robot_switch = True
                    self.send_msg_by_uid(u'[Robot]' + u'机器人已开启！', msg['to_user_id'])
                    return

    def get_cur_chat_uid(self, need_chat_uid = None, need_chat_type = None):
        if need_chat_uid is not None and need_chat_type is not None and need_chat_uid != self.robot_uid\
                and (need_chat_uid != self.cur_chat_uid or need_chat_type != self.cur_chat_type):   # 需要切换当前聊天用户
            if (datetime.today() - self.cur_chat_last_time).seconds > self.cur_chat_timeout_second and\
                    (self.wait_robot_dtime is None or (datetime.today() - self.wait_robot_dtime).seconds > self.cur_chat_timeout_second):     # 不存在等回复消息，或机器人回复消息超时时，进行切换
                self.wait_robot_dtime = None
                self.cur_chat_type = need_chat_type
                self.cur_chat_uid = need_chat_uid
                self.send_msg_by_uid(self.in_chat_tip_msg, self.cur_chat_uid)

        return self.cur_chat_uid if self.cur_chat_type == 4 else self.watch_gid

    def auto_proxy_reply_msg(self, msg, to_uid = None):    # 自动代理转发消息
        msg_type_id = msg['msg_type_id']
        if not self.robot_switch and msg_type_id != 3 and msg_type_id != 4:
            return

        cur_chat_id = self.get_cur_chat_uid(msg['user']['id'], msg_type_id)
        if msg['user']['id'] == self.robot_uid:    # 接收robot回复消息
            if self.wait_robot_dtime is not None and (datetime.today() - self.wait_robot_dtime).seconds < self.cur_chat_timeout_second:
                self.wait_robot_dtime = None
                to_uid = cur_chat_id
            else:
                self.wait_robot_dtime = None
                return
        elif to_uid == self.robot_uid:   # 代理与机器人聊天
            self.wait_robot_dtime = datetime.today()
            if msg['user']['id'] != cur_chat_id:
                self.need_chat_queue.put(msg)
                return

        if msg['content']['type'] == 0:
            if to_uid == self.robot_uid:
                self.send_msg_by_uid(msg['content']['data'], to_uid)
            else:
                self.send_msg_by_uid(u'助理：' + msg['content']['data'], to_uid)
        elif msg['content']['type'] == 3:
            fpath = os.path.join(self.temp_pwd, self.get_msg_img(msg['msg_id']))
            self.send_img_msg_by_uid(fpath, to_uid)
        elif msg['content']['type'] == 4:
            fpath = os.path.join(self.temp_pwd, self.get_voice(msg['msg_id']))
            self.send_file_msg_by_uid(fpath, to_uid)
        elif msg['content']['type'] == 13:
            fpath = os.path.join(self.temp_pwd, self.get_video(msg['msg_id']))
            self.send_file_msg_by_uid(fpath, to_uid)

    def handle_msg_all(self, msg):
        if not self.robot_switch and msg['msg_type_id'] != 1:
            return
        if msg['msg_type_id'] == 1 and msg['content']['type'] == 0:  # reply to self
            self.auto_switch(msg)
            return

        if msg['msg_type_id'] == 4 and msg['content']['type'] == 0:  # text message from contact
                self.auto_proxy_reply_msg(msg, self.robot_uid)
        elif msg['msg_type_id'] == 5 and msg['user']['id'] == self.robot_uid:  # text message from contact
            self.auto_proxy_reply_msg(msg)
        elif msg['msg_type_id'] == 3 and msg['user']['id'] == self.watch_gid:  # group text message
            if msg['content']['type'] != 0:
                self.auto_proxy_reply_msg(msg, self.robot_uid)
            elif 'detail' in msg['content'] and msg['content']['type'] == 0:
                my_names = self.get_group_member_name(msg['user']['id'], self.my_account['UserName'])
                if my_names is None:
                    my_names = {}
                if 'NickName' in self.my_account and self.my_account['NickName']:
                    my_names['nickname2'] = self.my_account['NickName']
                if 'RemarkName' in self.my_account and self.my_account['RemarkName']:
                    my_names['remark_name2'] = self.my_account['RemarkName']

                is_at = False
                is_at_me = False
                for detail in msg['content']['detail']:
                    if detail['type'] == 'at':
                        is_at = True
                        for k in my_names:
                            if my_names[k] and my_names[k] == detail['value']:
                                is_at_me = True
                                break
                if not is_at or is_at_me:
                    self.auto_proxy_reply_msg(msg, self.robot_uid)

    def handle_history_msg_all(self):
        queue = self.need_chat_queue
        new_queue = Queue.Queue()

        cur_chat_id = None

        while True:
            if queue.qsize() < 1:
                break
            else:
                msg = queue.get()
                if cur_chat_id is None:
                    cur_chat_id = self.get_cur_chat_uid(msg['user']['id'], msg['msg_type_id'])
                if cur_chat_id == msg['user']['id']:
                    self.handle_msg(msg)
                else:
                    new_queue.put(msg)
        self.need_chat_queue = new_queue

    def schedule(self):
        if self.robot_uid is None or self.watch_gid is None:
            for account in self.public_list:
                if self.robot_name == account['NickName']:
                    self.robot_uid = account['UserName']
                    print '    robot uid:', account['NickName'], self.robot_uid

            for account in self.group_list:
                watch_group_name = u'智能测试'
                if watch_group_name == account['NickName']:
                    self.watch_gid = account['UserName']
                    print '    watch group:', account['NickName'], self.watch_gid
        self.handle_history_msg_all()

def main():
    bot = XiaoBingWXBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'png'

    bot.run()


if __name__ == '__main__':
    main()
