# -*- coding: utf-8 -*-
"""
File Name: log.py
Author: 07xiaohei
Date: 2024-05-10
Version: 1.0
Description: nvd文件的处理，nvd是网络视频设备(network_video_device)的简写，一般为网络摄像头
"""

__all__ = ["Log_Processor"]

# 导入常用库
from home_security_surveillance.common import *

# 引入inspect库，用于获得函数的调用者信息
import inspect

## 日志文件的处理部分 ##

class Log_Processor(object):
    """
    Log_Processor(log_dir, log_name, level)
    日志处理器对象，用于创建日志文件并进行读写

    Parameters
    ----------
    log_dir : str
        日志的根目录
    log_name : str
        日志的文件名
    level : int
        数字形式的日志优先级，默认为INFO级别

    Attributes
    ----------
    strftime_all : str
        日志文件记录时间的格式，是类变量
    strftime_date : str
        日志文件记录日期的格式，是类变量
    strftime_time : str
        日志文件记录时分秒的格式，是类变量
    CRITICAL = logging.CRITICAL
        日志文件输出的消息级别，致命错误
    ERROR = logging.ERROR
        日志文件输出的消息级别，一般错误
    WARNING = logging.WARNING
        日志文件输出的消息级别，警告
    INFO = logging.INFO
        日志文件输出的消息级别，日常事务
    DEBUG = logging.DEBUG
        日志文件输出的消息级别，调试过程

    logger: Logger
        日志记录器对象的一个实例，用于记录活动过程中的运行信息和错误信息

    Notes
    -----
    对要使用的Logger的包装

    Examples
    --------
    """

    # 日志文件记录时间的格式，分别是全部的时间格式，日期的时间格式，时分秒的时间格式
    strftime_all = "%Y-%m-%d_%H-%M-%S"
    strftime_date = "%Y-%m-%d"
    strftime_time = "%H-%M-%S"

    # 日志文件消息级别
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG

    def __init__(self, log_dir: str,
                 log_name: str,
                 level: int = logging.INFO):
        """初始化日志记录器对象"""

        # 创建日志记录器对象
        self.logger = logging.getLogger(f"{log_name}_{level}")
        # 根据传入参数设置日志记录器的优先级
        self.logger.setLevel(level)
        # 创建文件处理器，文件目录和文件名为传入参数，使用追加模式和utf-8编码
        file_handler = logging.FileHandler(filename=os.path.join(log_dir, log_name),
                                           mode='a', encoding='utf-8')
        # 设置文件处理器的格式化内容
        # asctime是时间，格式为strftime_all
        # levelname是日志级别
        # frame_pathname是调用log_write函数的文件名
        # frame_funcName是调用log_write函数的名称
        # message是日志信息
        formatter = self.CustomFormatter(
            fmt='%(asctime)s - %(levelname)s in %(frame_filename)s function %(frame_funcName)s : %(message)s\n',
            datefmt=Log_Processor.strftime_all
        )
        file_handler.setFormatter(formatter)
        # 添加文件处理器
        self.logger.addHandler(file_handler)

    class CustomFormatter(logging.Formatter):
        def format(self, record):
            if not hasattr(record, 'frame_filename'):
                record.frame_filename = record.filename
            if not hasattr(record, 'frame_funcName'):
                record.frame_funcName = record.funcName
            return super().format(record)

    def log_write(self, content: Union[str, Exception], level: int):
        """

        Parameters
        ----------
        content : Union[str, Exception]
            写入日志的信息，可以是错误类型，也可以是字符串
        level : int
            写入日志的级别，包括CRITICAL、ERROR、WARNING、INFO、DEBUG五个级别
        Returns
        -------

        """

        # 获得调用该函数的文件名和调用该函数的函数名
        extra_frame = {'frame_filename': None, 'frame_funcName': None}

        # 获取调用者的信息相应信息
        caller_frame = inspect.stack()[1]
        extra_frame['frame_filename'] = os.path.basename(caller_frame[1])
        extra_frame['frame_funcName'] = caller_frame[3]

        if level == Log_Processor.CRITICAL:
            self.logger.critical(content, extra=extra_frame)
        elif level == Log_Processor.ERROR:
            self.logger.error(content, exc_info=True, extra=extra_frame)
        elif level == Log_Processor.WARNING:
            self.logger.warning(content, extra=extra_frame)
        if level == Log_Processor.INFO:
            self.logger.info(content, extra=extra_frame)
        if level == Log_Processor.DEBUG:
            self.logger.debug(content, extra=extra_frame)


# 模块测试部分
if __name__ == "__main__":
    # 加载日志处理器
    logger = Log_Processor("./", "test.log", logging.INFO)
    # 信息写入
    logger.log_write("test", Log_Processor.INFO)
    # 错误写入
    try:
        raise ValueError("test logging")
    except Exception as e:
        logger.log_write(e, Log_Processor.ERROR)
        logger.logger.error(e, exc_info=True)
