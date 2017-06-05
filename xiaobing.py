#!/usr/bin/env python
# coding: utf-8

from wxbot import *


class XiaoBingWXBot(WXBot):
    def __init__(self):
        WXBot.__init__(self)

        self.robot_switch = True
        self.robot_uid = None
        self.watch_gid = None

    def auto_switch(self, msg):
        msg_data = msg['content']['data']
        stop_cmd = [u'退下', u'走开', u'关闭', u'关掉', u'休息', u'滚开']
        start_cmd = [u'出来', u'启动', u'工作']

        for account in self.group_list:
            if msg_data == account['NickName']:
                self.watch_gid = account['UserName']
                print '    watch uid:', account['NickName'], self.watch_gid

        if self.robot_switch:
            for i in stop_cmd:
                if i == msg_data:
                    self.robot_switch = False
                    self.send_msg_by_uid(u'[Robot]' + u'机器人已关闭！', msg['to_user_id'])
        else:
            for i in start_cmd:
                if i == msg_data:
                    self.robot_switch = True
                    self.send_msg_by_uid(u'[Robot]' + u'机器人已开启！', msg['to_user_id'])

    def handle_msg_all(self, msg):
        if not self.robot_switch and msg['msg_type_id'] != 1:
            return
        if msg['msg_type_id'] == 1 and msg['content']['type'] == 0:  # reply to self
            self.auto_switch(msg)
        elif msg['msg_type_id'] == 4 and msg['content']['type'] == 0:  # text message from contact
            print '    receive msg:', msg['user']['id'], msg['content']['data']
        elif msg['msg_type_id'] == 5 or msg['msg_type_id'] == 3 and msg['content']['type'] != 0:  # text message from contact
            uid = self.watch_gid
            if msg['msg_type_id'] == 3:
                uid = self.robot_uid

            if msg['content']['type'] == 0:
                print '    receive gongzhong msg:', msg['user']['id'], msg['content']['data']
                self.send_msg_by_uid(msg['content']['data'], uid)
            elif msg['content']['type'] == 3:
                fpath = os.path.join(self.temp_pwd, self.get_msg_img(msg['msg_id']))
                self.send_img_msg_by_uid(fpath, uid)
            elif msg['content']['type'] == 4:
                fpath = os.path.join(self.temp_pwd, self.get_voice(msg['msg_id']))
                self.send_file_msg_by_uid(fpath, uid)
            elif msg['content']['type'] == 13:
                fpath = os.path.join(self.temp_pwd, self.get_video(msg['msg_id']))
                self.send_file_msg_by_uid(fpath, uid)

        elif msg['msg_type_id'] == 3 and msg['content']['type'] == 0:  # group text message
            if 'detail' in msg['content'] and msg['user']['id'] == self.watch_gid:
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
                    # src_name = msg['content']['user']['name']
                    # reply = 'to ' + src_name + ': '
                    print '    receive group msg:', msg['content']['user']['id'], msg['content']['desc']
                    # if msg['content']['type'] == 0:  # text message
                    #     reply += self.tuling_auto_reply(msg['content']['user']['id'], msg['content']['desc'])
                    # else:
                    #     reply += u"对不起，只认字，其他杂七杂八的我都不认识，,,Ծ‸Ծ,,"
                    # self.send_msg_by_uid(reply, msg['user']['id'])
                    self.send_msg_by_uid(msg['content']['desc'], self.robot_uid)

    def schedule(self):
        if self.robot_uid == None or self.watch_gid == None:
            for account in self.public_list:
                if u'小冰' == account['NickName']:
                    self.robot_uid = account['UserName']
                    print '    robot uid:', account['NickName'], self.robot_uid

            for account in self.group_list:
                watch_group_name = u'到怀远的古惑仔们'
                # watch_group_name = u'智能测试'
                if watch_group_name == account['NickName']:
                    self.watch_gid = account['UserName']
                    print '    watch uid:', account['NickName'], self.watch_gid

def main():
    bot = XiaoBingWXBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'png'

    bot.run()


if __name__ == '__main__':
    main()

