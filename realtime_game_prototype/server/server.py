# -*- coding: utf-8 -*-

import weakref
import time
import gevent
from gevent.queue import Queue
from haven import GHaven
from netkit.box import Box

from share import cmds
from share import constants


def create_app():

    app = GHaven(Box)

    app.conn_id_inc = 0
    app.conn_dict = weakref.WeakValueDictionary()

    # 消息
    app.msg_queue = Queue()

    # 核心帧数index
    app.frame_index = 0

    def game_loop():
        # 游戏帧循环
        frame_interval = 1.0 / constants.KERNEL_FRAME_RATE
        # 每一帧，从 net_msg_queue 将数据取出来
        while True:
            time.sleep(frame_interval)

    @app.create_conn
    def create_conn(conn):
        # 自增
        app.conn_id_inc += 1
        conn.conn_id = app.conn_id_inc

        # 还没有准备好
        conn.user_ready = False

        # 析构会自动删除
        app.conn_dict[conn.conn_id] = conn

    @app.close_conn
    def close_conn(conn):
        app.conn_dict.pop(conn.conn_id, None)

    @app.create_worker
    def create_worker():
        """
        启动游戏循环
        :return:
        """
        gevent.spawn(game_loop)

    @app.route(cmds.CMD_USER_READY)
    def user_ready(request):
        if len(app.conn_dict) < 2 or filter(lambda x: not x.user_ready, app.conn_dict):
            return

        # 人数大于等于2，并且所有人都已经准备好了
        # 就可以下发游戏开始通知了

        box = Box()
        box.cmd = cmds.EVT_GAME_START

        data = box.pack()

        for conn in request.conn_dict.values():
            conn.write(data)

    return app
