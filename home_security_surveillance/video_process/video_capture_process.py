# -*- coding: utf-8 -*-
"""
File Name: video_capture_process.py
Author: 07xiaohei
Date: 2024-05-15
Version: 1.0
Description: 用于opencv在捕捉url信息减少超时时间的进程类
"""
import queue

# 引入常用库
from home_security_surveillance.common import *

__all__ = ["Video_Capture_Process"]

class Video_Capture_Process(multiprocessing.Process):
    """
    Video_Capture_Process(url, timeout, result_queue)

    多进程类，利用opencv的VideoCapture函数测试url是否可以获得视频流

    Parameters
    ----------
    url : str
        用于捕捉视频流的url地址
    result_queue : multiprocessing.Queue
        用于接收创建的VideoCapture对象是否成功标志的队列

    Attributes
    ----------
    url : str
        用于捕捉视频流的url地址
    result_queue : multiprocessing.Queue
        用于接收创建的VideoCapture对象是否成功标志的队列
    """
    def __init__(self, url: str, result_queue: multiprocessing.Queue):
        # 记录变量
        self.url = url
        self.result_queue = result_queue
        super().__init__()

    def run(self):
        """进程处理的部分,向队列输入一个布尔值"""
        # 根据视频源创建一个VideoCapture对象，用于从视频源中读取帧
        capture = cv.VideoCapture(self.url, apiPreference=cv.CAP_ANY)
        # 创建成功，且尝试打开成功，向队列输入True
        if capture.isOpened():
            self.result_queue.put(True)
        # 否则向队列输入False
        else:
            self.result_queue.put(False)
        capture.release()
