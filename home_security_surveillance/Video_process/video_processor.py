# -*- coding: utf-8 -*-
"""
File Name: video_processor.py
Author: 07xiaohei
Date: 2024-05-13
Version: 1.0
Description: 处理视频流的核心类
"""
# 引入常用库
from home_security_surveillance.Common import *
# 引入PyCameraList.camera_device库的list_video_devices函数，用于列出所有可用的视频源
from PyCameraList.camera_device import list_video_devices
# 引入file_process包
from home_security_surveillance.File_process import *
# 引入video_capture_process库
from home_security_surveillance.Video_process.video_capture_process import *
# 引入video_detect库
from home_security_surveillance.Video_process.video_detect import *
# 引入Exception_process库
from home_security_surveillance.Exception_process import *
# 引入synchronize库的Event对象
from multiprocessing import synchronize

__all__ = ["Video_Processor"]

class Video_Processor(object):
    """
    Video_Processor(url_capture_time_out, root)

    从视频源处获得视频流并进行处理的相关类，是家庭监控系统的核心处理部分

    Parameters
    ----------
    url_capture_time_out : int
        opencv在捕捉网络摄像头url视频流时的超时时间设置，各协议统一，且应小于opencv已设置的时间
        此处最大为15s，默认值为10s，最大请尽量小于15s
    event: synchronize.Event
        ui界面创建对象时传递的事件，在该类传递事件内标记设置为False时结束任务退出进程，默认为None
    return_value : multiprocessing.Value
        ui界面创建对象时传递的共享内存变量，默认为None

    Attributes
    ----------
    ui_event: synchronize.Event
        ui界面创建对象时传递的事件，在该类传递事件内标记设置为False时结束任务退出进程，默认为None
    ui_value : multiprocessing.Value
        ui界面创建对象时传递的共享内存变量，默认为None

    create_time : str
        创建该对象的时间，字符串类型，格式与log.py中Log_Processor的strftime_all相同
    url_capture_time_out : int
        opencv在捕捉网络摄像头url视频流时的超时时间设置，各协议统一，且应小于opencv已设置的时间
        此处最大为15s，默认值为10s，最大请尽量小于15s
    config_data : dict
        配置文件的字典格式，每个元素为一个键值对，键为配置文件的属性名，值为配置文件的属性值

    local_video_device_list : List[ Tuple[ Union[int,str],str ] ]
        关于本地视频设备的一个列表，每个元素为一个元组，每个元组内有两个子元素
        每个元组的第一个元素是视频源的相关信息作为show_video_in_cv函数的输入，用于opencv库从视频源中获得视频流
        每个元组的第二个元素是视频源的相关说明
    logger : Log_Processor
        日志处理器对象的一个实例，用于记录该类活动过程中的运行信息和错误信息
    nvd_processor : Nvd_processor
        网络视频设备处理器对象的一个实例，用于处理网络应用设备的加载、访问和修改
    hs_processor : History_video_processor
        历史视频处理器对象的一个实例，用于处理对历史视频的加载、访问和识别
    video_detector : Video_Detector
        视频检测处理器对象的一个实例，使用基于yolov8的识别模型对视频流进行监测
    warning_processor : Warning_processor
        异常警报处理器对象的一个实例，使用smtplib库发送邮件，pygame库播放音频，tkinter库弹出警告窗口

    _load_flag : List[bool, bool, bool]
        标记上述的本地视频设备、网络视频设备和历史视频处理器的加载是否成功且不为空，便于后续处理时确定是否可用

    Notes
    -----
    视频流的来源包括本地视频设备(如USB摄像头)，网络视频设备（如ip摄像头）和历史监控视频三种
    传入video_type=1对应本地监视器设备，video_type=2对应网络视频设备，video_type=3对应历史监控视频
    Examples
    --------
    """
    # 统一使用的视频格式
    _video_suffix = "avi"
    # 可使用的最大分辨率
    _video_resolution = (1280, 720)

    def __init__(self, url_capture_time_out: int = 10,
                 event: synchronize.Event = None, return_value: multiprocessing.Value = None):
        """初始化Video_processor对象"""

        # 获得格式化的当前时间，作为该类的创建时间
        self.create_time = datetime.datetime.now().strftime(Log_Processor.strftime_all)

        # 记录超时时间
        self.url_capture_time_out = url_capture_time_out
        # 记录共享变量和事件
        self.ui_event = event
        self.ui_value = return_value
        # 加载json格式的配置文件
        try:
            self.config_data, invalid_config_data = load_config(relative=False)

        # 如果解析失败，对错误信息的处理
        except json.JSONDecodeError as e:
            # 创建默认的日志处理器对象输出错误
            self.logger = self._create_logger()
            self.logger.log_write(e, Log_Processor.ERROR)
            ### 后续的处理（前端部分），这里要输出配置文件解析失败的错误信息
            ### 也就是Config下面根源的那个config.json文件解析失败信息，只有这个解析正确才能保研后续的全部加载是一定成功的
            pass

        # 解释成功后的处理
        else:
            # 创建日志文件,输出信息
            self.logger = self._create_logger(self.config_data["log-directory"], Log_Processor.INFO)
            # 如果有无效键值对，输出处理信息
            if invalid_config_data:
                self.logger.log_write(f"Have deleted invaild item(s) in " +
                                      f"{os.path.abspath(config_file)}: " +
                                      f"{invalid_config_data}", Log_Processor.INFO)
            # 输出加载成功信息
            self.logger.log_write(f"Successfully loaded configuration file "
                                  f"{os.path.abspath(config_file)}", Log_Processor.INFO)

        # 加载视频设备的相关信息
        self._load_video_sourse()

        # 加载视频监测处理器
        self.video_detector = Video_Detector(root_dir=self.config_data["model-directory"],
                                             use_defalut_parameter=False)
        # 输出加载成功信息
        self.logger.log_write(f"Successfully loaded video detector "
                              f"the root dir is{self.config_data['model-directory']}",
                              Log_Processor.INFO)

        # 加载异常警报处理器
        self.warning_processor = Warning_Processor(warning_dir=
                                                   self.config_data["exception-monitoring-directory"])
        # 输出加载成功信息
        self.logger.log_write(f"Successfully loaded warning processor "
                              f"the root dir is{self.config_data['exception-monitoring-directory']}",
                              Log_Processor.INFO)

    def _create_logger(self, log_dir: str = config_defaluts["log-directory"],
                       level: int = Log_Processor.INFO):
        """
        创建日志处理器对象函数

        Parameters
        ----------
        log_dir : str
            日志的根目录，默认为log.py中定义的config_defaults变量的log-directory键值
        level : int
            数字形式的日志优先级，默认为INFO级别

        Returns
        -------
        logger : Log_Processor
            返回一个日志处理器对象
        """

        # 创建的日志处理器的处理文件名为该类的创建时间
        return Log_Processor(log_dir, self.create_time + ".log", level)

    def _load_video_sourse(self):
        """加载视频资源函数"""

        # 标记加载成功性
        self._load_flag = [True, True, True]

        # 获得所有本地可用视频设备的列表并进行日志记录
        self.local_video_device_list = list_video_devices()
        # 判断加载后本地视频设备是否为空
        if not self.local_video_device_list:
            self.logger.log_write(f"The loaded local video device is empty.", Log_Processor.WARNING)
            self._load_flag[0] = False
        else:
            self.logger.log_write(f"Successfully loaded local video device:\n"
                                  f"{self.local_video_device_list}",
                                  Log_Processor.INFO)

        # 获得网络视频设备配置文件的所有url结果，每个url的信息对应列表的元素，类型为dict，并进行日志记录
        try:
            self.nvd_processor = Nvd_Processor(self.config_data["IP-video-device-file"], re_parse=True)
        except json.decoder.JSONDecodeError as e:
            # 加载出错时抛出错误，需要修改错误信息，将文件名信息加入其中
            new_e_msg = f"Error decoding JSON in file" + \
                        f"{self.config_data['IP-video-device-file']}: {e.msg}"
            self.logger.log_write(f"{new_e_msg}", Log_Processor.ERROR)

        # 判断加载后网络视频设备是否为空
        if not self.nvd_processor.nvd_config_data:
            self.logger.log_write(f"The loaded saved network video device is empty",
                                  Log_Processor.WARNING)
            self._load_flag[1] = False
        else:
            self.logger.log_write(f"Successfully loaded network video device",
                                  Log_Processor.INFO)

        # 加载所有历史保存视频视频处理器对象
        self.hs_processor = History_Video_Processor(self.config_data["history-video-directory"],
                                                    self._video_suffix)
        # 判断历史保存视频是否为空
        if not self.hs_processor.hv_dict:
            self.logger.log_write(f"The loaded history video directory is empty",
                                  Log_Processor.WARNING)
            self._load_flag[2] = False
        else:
            self.logger.log_write(f"Successfully loaded history video processor",
                                  Log_Processor.INFO)

    def update_local_video_sourse(self) -> bool:
        """
        更新本地视频设备
        Returns
        -------
        flag : bool
            是否完成了更新，如更新返回True，否则为False
        """
        temp = list_video_devices()
        # 判断加载后本地视频设备是否为空
        # 如果为空且之前不为空
        if temp != self.local_video_device_list:
            self.logger.log_write(f"The loaded local video device has changed, now the"
                                  f"local video device:\n"
                                  f"{self.local_video_device_list}", Log_Processor.INFO)
            # 更新变量和flag
            if temp and not self.local_video_device_list:
                self._load_flag[0] = True
            elif not temp and self.local_video_device_list:
                self._load_flag[0] = False
            self.local_video_device_list = temp
            return True

        return False

    def load_local_video_device(self, video_sourse: int = 0,
                                flag_visibility: bool = True,
                                flag_save: bool = True,
                                flag_detect: bool = True,
                                video_detect_type: int = 1,
                                video_detect_sensitivity: int = 0
                                ) -> int:
        """
        从本地视频设备利用opencv库加载视频流，根据传入的本地视频设备号来捕捉视频信息

        Parameters
        ----------
        video_sourse : int
            要捕获的本地视频设备的索引号，用于opencv库从视频源处获得视频流
        flag_visibility : bool
            控制opencv在读取视频流时是否展示，True时展示视频，False时不展示，可用于后台处理视频
        flag_save : bool
            控制opencv在读取视频六时是否保存，True时保存视频，False时不保存
        flag_detect : bool
            控制视频流是否需要进行监测，目标追踪，默认为True
        video_detect_type : int
            控制视频流监测的类型，0为全部监测，1为只监测火焰，2为只监测人，3为检测异常情况
        video_detect_sensitivity : int
            控制视频流在监测时的敏感度，0为低敏感度，1为高敏感度
        Returns
        --------
        res : int
            返回一个整型，每个值对应一个错误类型或者正确类型
            0则说明读取、展示和保存成功
            -1则说明打开摄像头失败
            -2则说明读取摄像头下一帧失败或者摄像头意外关闭
            -3则说明指定保存视频文件时，创建目录或打开视频文件失败
            1说明本地视频设备为空
            2说明传入索引号超过了本地视频设备列表大小

        Notes
        -----
        为了加速模型识别处理速度，创建一个进程单独执行识别功能，与该进程的通信使用两个多进程队列multiprocessing.Queue
        一个是frame_queue，用于将捕捉的视频帧在处理后传给识别进程
        一个是result_queue，用于将识别进程识别到错误的获得的错误类型和置信度返回给该进程
        """

        # 检查本地设备是否为空
        if not self._load_flag[0]:
            self.logger.log_write("Can't load local video device, the local video device is no exist.",
                                  Log_Processor.ERROR)
            self.ui_value.value = 1
            return 1

        # 检查传入索引号是否超过了列表大小
        if video_sourse >= len(self.local_video_device_list):
            self.logger.log_write(f"The {video_sourse} is out of " +
                                  f"the length {len(self.local_video_device_list):} " +
                                  f"of local video device list.", Log_Processor.ERROR)
            self.ui_value.value = 2
            return 2

        # 根据视频源创建一个VideoCapture对象，用于从视频源中读取帧
        video_stream = cv.VideoCapture(video_sourse, apiPreference=cv.CAP_ANY)

        # 判断是否打开，成功则进行下一步的处理
        if video_stream.isOpened():
            # 更新共享变量以说明进程启动成功
            self.ui_value.value = -9
            # 获得视频流参数，包括宽度、高度和帧率，转为整型
            real_width = int(video_stream.get(cv.CAP_PROP_FRAME_WIDTH))
            real_height = int(video_stream.get(cv.CAP_PROP_FRAME_HEIGHT))
            real_fps = int(video_stream.get(cv.CAP_PROP_FPS))

            # 如果超过了要求大小，限制其大小为720p
            # 需要注意的是，此处的限制只能对能够修改对应效果的摄像头进行处理，否则是无效的
            flag_resize = 0
            # 横屏限制
            if real_width > real_height:
                if real_width > self._video_resolution[0] or real_height > self._video_resolution[1]:
                    video_stream.set(cv.CAP_PROP_FRAME_WIDTH, self._video_resolution[0])
                    video_stream.set(cv.CAP_PROP_FRAME_HEIGHT, self._video_resolution[1])
                    width = video_stream.get(cv.CAP_PROP_FRAME_WIDTH)
                    height = video_stream.get(cv.CAP_PROP_FRAME_HEIGHT)
                else:
                    width, height = real_width, real_height
                if width > self._video_resolution[0] or height > self._video_resolution[1]:
                    flag_resize = 1
            # 竖屏限制
            else:
                if real_width > self._video_resolution[1] or real_height > self._video_resolution[0]:
                    video_stream.set(cv.CAP_PROP_FRAME_WIDTH, self._video_resolution[1])
                    video_stream.set(cv.CAP_PROP_FRAME_HEIGHT, self._video_resolution[0])
                    width = video_stream.get(cv.CAP_PROP_FRAME_WIDTH)
                    height = video_stream.get(cv.CAP_PROP_FRAME_HEIGHT)
                else:
                    width, height = real_width, real_height
                if width > self._video_resolution[1] or height > self._video_resolution[0]:
                    flag_resize = 2
            # 帧率限制
            # fps为90000表示时钟频率，不做处理
            if real_fps != 90000 and real_fps > 30:
                video_stream.set(cv.CAP_PROP_FPS, 30)
                fps = video_stream.get(cv.CAP_PROP_FPS)
            elif real_fps == 90000:
                fps = 30
            else:
                fps = real_fps
            ## 亮度、对比度、饱和度、色调和曝光调整
            # video_stream.set(cv.CAP_PROP_BRIGHTNESS, 1)
            # video_stream.set(cv.CAP_PROP_CONTRAST, 40)
            # video_stream.set(cv.CAP_PROP_SATURATION, 50)
            # video_stream.set(cv.CAP_PROP_HUE, 50)
            # video_stream.set(cv.CAP_PROP_EXPOSURE, 50)

            # 日志输出
            self.logger.log_write(f"Load the local video device " +
                                  f"{self.local_video_device_list[video_sourse]}\n" +
                                  f"The video raal width is {real_width}, " +
                                  f"the video raal height is {real_height}, " +
                                  f"and the raal fps is {real_fps}.\n" +
                                  f"The setting video width is {width} " +
                                  f"athe setting video width is {height} " +
                                  f"The setting video width is {fps} ",
                                  Log_Processor.INFO)

            # 如果需要识别视频，创建保存帧的读取队列和结果队列
            frame_queue = None
            result_queue = None
            if flag_detect:
                frame_queue = multiprocessing.Queue()
                result_queue = multiprocessing.Queue()
                # 创建进程，传入参数并运行
                video_detect_process = multiprocessing.Process(
                    target=self.video_detector.detect,
                    args=(frame_queue, result_queue, video_detect_type),
                    kwargs={"sensitivity": video_detect_sensitivity})
                video_detect_process.start()
                self.logger.log_write("Start running video detect process",
                                      Log_Processor.INFO)

            # 如果需要可视化，创建视频窗口，设置相应参数
            Window_name = ""
            if flag_visibility:
                # 窗口名
                Window_name = f"{self.local_video_device_list[video_sourse][1]}"
                # WINDOW_NORMAL控制窗口可以放缩，WINDOW_KEEPRATIO控制窗口缩放的过程中保持比率
                # WINDOW_GUI_EXPANDED控制使用新版本功能增强的GUI窗口
                cv.namedWindow(Window_name, flags=cv.WINDOW_NORMAL | cv.WINDOW_KEEPRATIO |
                                                  cv.WINDOW_GUI_EXPANDED)
                # 大小设置为720p的大小
                if real_width > real_height:
                    cv.resizeWindow(Window_name, 1280, 720)
                elif real_width < real_height:
                    cv.resizeWindow(Window_name, 720, 1280)
                else:
                    cv.resizeWindow(Window_name, 720, 720)

            # 如果需要保存视频，在指定目录处创建视频文件，用于写入视频帧
            video_out = None
            if flag_save:
                # 根据当前时间生成文件路径并更新历史视频处理器中的hv_dict(在函数中完成)
                try:
                    save_path = self.hs_processor.generate_video_file(
                        datetime.datetime.now().strftime(Log_Processor.strftime_all))
                # 如果目录已存在且再次创建
                except FileExistsError as e:
                    self.logger.log_write(f"Fail to create save video dir: " + e.strerror,
                                          Log_Processor.ERROR)
                    self.ui_value.value = -3
                    return -3
                # 如果路径有错误
                except OSError as e:
                    self.logger.log_write(f"Fail to create save video dir: " + e.strerror,
                                          Log_Processor.ERROR)
                    self.ui_value.value = -3
                    return -3
                # 无错误则输入视频流至文件中
                else:
                    # 声明编码保存方式
                    fourcc = cv.VideoWriter.fourcc(*"DIVX")
                    # 利用VideoWriter保存视频，文件路径为生成路径，帧率和分辨率统一为限制后的视频大小和帧率，彩色模式
                    video_out = cv.VideoWriter(save_path, fourcc, fps, (width, height), True)
                    # 如果打开成功，日志记录
                    if video_out.isOpened():
                        self.logger.log_write(f"Create save video file: {save_path}",
                                              Log_Processor.INFO)
                    # 如果打开失败，删除历史视频处理器中的hv_dict信息
                    else:
                        self.hs_processor.delete_new_video_file(save_path)
                        self.logger.log_write(f"Fail to create save video file: {save_path}",
                                              Log_Processor.ERROR)
                        self.ui_value.value = -3
                        return -3

            # 循环部分，用于读取视频
            # skip用于跳帧
            skip = 0
            Warning_thread = None
            while True:
                # 如果ui界面触发了关闭事件，退出进程
                if self.ui_event.is_set():
                    if flag_save:
                        video_out.release()
                    if flag_visibility:
                        cv.destroyWindow(Window_name)
                    video_stream.release()
                    # 由于没有终止视频帧None，手动传输结束识别进程
                    if flag_detect:
                        frame_queue.put(None)
                    break

                success = video_stream.grab()
                # 如果摄像头读取失败，日志记录，结束运行，释放视频捕捉对象，销毁窗口
                if not success:
                    self.logger.log_write(f"Fail to read the video of the local video device " +
                                          f"{self.local_video_device_list[video_sourse][1]}. " +
                                          f"Please check the device.",
                                          Log_Processor.ERROR)
                    if flag_save:
                        video_out.release()
                    if flag_visibility:
                        cv.destroyWindow(Window_name)
                    video_stream.release()
                    # 由于没有终止视频帧None，手动传输结束识别进程
                    if flag_detect:
                        frame_queue.put(None)
                    self.ui_value.value = -2
                    return -2

                # 跳帧或者视频解码
                skip += 1
                skip %= 4
                if 15 <= fps < 60 and skip % 2 == 1:
                    continue
                elif fps >= 60 and skip >= 1:
                    continue
                else:
                    _, frame = video_stream.retrieve()

                # 如果视频帧分辨率大于阈值，根据横竖屏重整为阈值
                if flag_resize == 1:
                    frame = cv.resize(frame, (self._video_resolution[0], self._video_resolution[1]),
                                      interpolation=cv.INTER_LINEAR)
                elif flag_resize == 2:
                    frame = cv.resize(frame, (self._video_resolution[1], self._video_resolution[0]),
                                      interpolation=cv.INTER_LINEAR)

                # 识别视频流的操作，放入帧并检查结果
                if flag_detect:
                    frame_queue.put(frame)
                    # 如果结果队列非空，说明出现了错误
                    if not result_queue.empty():
                        # 错误类型是一个列表，第一个元素是错误编码，第二个是各错误的置信度
                        warning_info = result_queue.get()
                        now_time = datetime.datetime.now().strftime(Log_Processor.strftime_all)
                        # 创建线程，并用报警器进行处理
                        Warning_thread = threading.Thread(target=self.warning_processor.warning_process,
                                                          args=(warning_info[0], now_time, warning_info[1],
                                                                video_detect_sensitivity))
                        Warning_thread.start()
                        self.logger.log_write(f"{now_time} have exception", Log_Processor.WARNING)

                # 可见窗口时的操作
                if flag_visibility:
                    # 将当前帧在窗口中展示
                    cv.imshow(Window_name, frame)
                    # 按'q'和'ESC'键退出，释放视频捕捉对象，销毁窗口
                    cv2key = cv.waitKey(1)
                    if cv2key & 0xFF == ord('q') or cv2key & 0xFF == 27:
                        cv.destroyWindow(Window_name)
                        if flag_save:
                            video_out.release()
                        video_stream.release()
                        # 由于没有终止视频帧None，手动传输结束识别进程
                        if flag_detect:
                            frame_queue.put(None)
                        break
                    # # 如果s键按下，则进行图片保存
                    # elif cv2key == ord('s'):
                    #     # 记录当前时间
                    #     now_time = datetime.datetime.now().strftime(Log_Processor.strftime_all)
                    #     # 写入图片 并命名图片为 图片序号.png
                    #     cv.imwrite(f"{now_time}.png", frame)
                    # 点击"x"关闭之后退出
                    if cv.getWindowProperty(Window_name, cv.WND_PROP_VISIBLE) < 1:
                        if flag_save:
                            video_out.release()
                        video_stream.release()
                        # 由于没有终止视频帧None，手动传输结束识别进程
                        if flag_detect:
                            frame_queue.put(None)
                        break

                # 保存文件时的操作
                if flag_save:
                    # 注意要重写图像大小，否则分辨率不一致时会报错
                    write_frame = cv.resize(frame, (width, height), interpolation=cv.INTER_LINEAR)
                    video_out.write(write_frame)

        # 打开失败则输出错误错误到日志文件中
        else:
            self.logger.log_write(f"Fail to load the local video device " +
                                  f"{self.local_video_device_list[video_sourse][1]}",
                                  Log_Processor.ERROR)
            self.ui_value.value = -1
            return -1

        # 正常退出
        self.logger.log_write(f"Stop using the local video device " +
                              f"{self.local_video_device_list[video_sourse][1]}",
                              Log_Processor.INFO)
        self.ui_value.value = 0
        return 0

    @staticmethod
    def _network_device_visibility(vis_frame_queue: multiprocessing.Queue,
                                   vis_result_queue: multiprocessing.Queue,
                                   video_sourse: Union[int, str],
                                   real_width: int, real_height: int):
        """
        网络ip摄像头使用rtsp格式监控时会有大幅度的速度降低，此处使用新进程创建窗口
        Parameters
        ----------
        vis_frame_queue : multiprocessing.Queue
            接收视频帧队列
        vis_result_queue: multiprocessing.Queue
            返回视频帧处理结果队列
        video_sourse : Union[int, str]
            传入的ip或者url字符串，或者是已存储url的索引值
        """
        # 窗口名
        Window_name = f"{video_sourse}"
        # WINDOW_NORMAL控制窗口可以放缩，WINDOW_KEEPRATIO控制窗口缩放的过程中保持比率
        # WINDOW_GUI_EXPANDED控制使用新版本功能增强的GUI窗口
        cv.namedWindow(Window_name, flags=cv.WINDOW_NORMAL | cv.WINDOW_KEEPRATIO |
                                          cv.WINDOW_GUI_EXPANDED)
        # 大小设置为720p的大小
        if real_width > real_height:
            cv.resizeWindow(Window_name, 1280, 720)
        elif real_width < real_height:
            cv.resizeWindow(Window_name, 720, 1280)
        else:
            cv.resizeWindow(Window_name, 720, 720)

        # 获得当前时间，记录是否等待
        flag_wait = False
        start_wait_time = time.time()
        # 主循环
        while True:
            # 判断接收视频帧队列是否为空
            if not vis_frame_queue.empty():
                # 非空，重置等待标志，并获得每一帧进行处理
                if flag_wait:
                    flag_wait = False
                frame = vis_frame_queue.get()

                # 如果不是None
                if frame is not None:
                    # 将当前帧在窗口中展示
                    cv.imshow(Window_name, frame)
                    # 按'q'和'ESC'键退出，释放视频捕捉对象，销毁窗口
                    cv2key = cv.waitKey(1)
                    if cv2key & 0xFF == ord('q') or cv2key & 0xFF == 27:
                        for i in range(vis_frame_queue.qsize()):
                            vis_frame_queue.get()
                        cv.destroyWindow(Window_name)
                        vis_result_queue.put(True)
                        vis_result_queue.close()
                        vis_result_queue.join_thread()
                        return
                    # # 如果s键按下，则进行图片保存
                    # elif cv2key == ord('s'):
                    #     # 记录当前时间
                    #     now_time = datetime.datetime.now().strftime(Log_Processor.strftime_all)
                    #     # 写入图片 并命名图片为 图片序号.png
                    #     cv.imwrite(f"{now_time}.png", frame)
                    # 点击"x"关闭之后退出
                    if cv.getWindowProperty(Window_name, cv.WND_PROP_VISIBLE) < 1:
                        for i in range(vis_frame_queue.qsize()):
                            vis_frame_queue.get()
                        vis_result_queue.put(True)
                        vis_result_queue.close()
                        vis_result_queue.join_thread()
                        return

                # 如果为None，说明读取结束
                else:
                    for i in range(vis_frame_queue.qsize()):
                        vis_frame_queue.get()
                    cv.destroyWindow(Window_name)
                    return

            # 接收视频帧队列为空
            else:
                # 如果此前未进入等待状态，开始等待，并计时
                if not flag_wait:
                    flag_wait = True
                    start_wait_time = time.time()
                    continue
                # 如果此前进入了等待状态，判断等待时间是否超过了15s
                else:
                    # 如果超过了，说明可视化超时等待，结束运行
                    if time.time() - start_wait_time >= 15:
                        # 清空过程中传入队列的视频帧并关闭队列
                        for i in range(vis_frame_queue.qsize()):
                            vis_frame_queue.get()
                        vis_result_queue.close()
                        # 为返回视频帧处理结果队列传入结束运行帧，关闭队列，等待发送结束
                        vis_result_queue.put(False)
                        vis_result_queue.close()
                        vis_result_queue.join_thread()
                        return

    def load_network_video_device(self, video_sourse: Union[int, str] = 0,
                                  flag_visibility: bool = True,
                                  flag_save: bool = True,
                                  flag_detect: bool = True,
                                  video_detect_type: int = 1,
                                  video_detect_sensitivity: int = 0,
                                  video_protocol_type: str = "RTSP",
                                  ) -> int:
        """
        从网络视频设备利用opencv库加载视频流，根据传入的url、ip或者已存储url的索引值来捕捉视频信息

        Parameters
        ----------
        video_sourse : Union[int, str]
            传入的ip或者url字符串，或者是已存储url的索引值
        flag_visibility : bool
            控制opencv在读取视频流时是否展示，True时展示视频，False时不展示，可用于后台处理视频
        flag_save : bool
            控制opencv在读取视频流时是否保存，True时保存视频，False时不保存
        flag_detect : bool
            控制视频流是否需要进行监测，目标追踪，默认为True
        video_detect_type : int
            控制视频流监测的类型，0为全部监测，1为只监测火焰，2为只监测人，3为检测异常情况
        video_detect_sensitivity : int
            控制视频流在监测时的敏感度，0为低敏感度，1为高敏感度
        video_protocol_type : str
            读取视频流时网络视频设备使用的传输协议，默认为RSTP

        Returns
        --------
        res : int
            返回一个整型，每个值对应一个错误类型或者正确类型
            0则说明读取、展示和保存成功
            -1则说明打开摄像头失败
            -2则说明读取摄像头下一帧失败或者摄像头意外关闭
            -3则说明指定保存视频文件时，创建目录或打开视频文件失败
            1则说明网络视频设备为空
            2则说明网络设备视频传输协议不支持
            3则说明无法从url处获得视频流，即VideoCapture超时，与打开摄像头失败不同
        """

        # 如果加载的网络视频设备为空，则必须是url或者ip，不能对空字典做索引
        if not self._load_flag[1]:
            if isinstance(video_sourse, int):
                self.logger.log_write("Can't load the saved network video device, "
                                      "the saved network video device is no exist.",
                                      Log_Processor.ERROR)
                self.ui_value.value = 1
                return 1

        # 验证协议可用性
        protocol_index = self.nvd_processor.vaild_protocol(video_protocol_type)
        # 不可用则写入错误信息返回错误
        if protocol_index == 0:
            self.logger.log_write(f"The video transmission transprotocol " +
                                  f"{video_protocol_type} is not supported.",
                                  Log_Processor.ERROR)
            self.ui_value.value = 2
            return 2

        # 根据传入信息获得网络视频设备的url地址，用于opencv的读取
        # 记录传入信息类型字典，主要用于说明type_flag的值的每类对应情况
        type_flag_dict = {1: "int", 2: "no_exist_ip", 3: "exist_ip",
                          4: "no_exist_url", 5: "exist_url"}
        type_flag = 1

        # 如果是索引，直接使用存储的url地址即可
        if isinstance(video_sourse, int):
            for i in self.nvd_processor.nvd_config_data:
                if i["index"] == video_sourse:
                    video_sourse = i["url"]

        # 如果不是，则检验是否为ip
        elif self.nvd_processor.vaild_ip(video_sourse):
            # 如果是，根据ip查找已保存的url中是否有此ip
            ip_url = self.nvd_processor.from_ip_find_url(video_sourse)
            # 如果不存在，默认无账号密码、无端口，直接使用{protocol}://{ip}的格式
            if ip_url == "":
                video_sourse = self.nvd_processor.video_trans_protocol_dict[protocol_index] \
                               + video_sourse
                # 类型记录
                type_flag = 2
            # 如果存在，修改其为对应的url地址
            else:
                video_sourse = ip_url
                # 类型记录
                type_flag = 3

        # 如果不是ip，则认为是一个url
        else:
            # 检验是否存在
            for i in self.nvd_processor.nvd_config_data:
                # 存在，类型记录
                if i["url"] == video_sourse:
                    type_flag = 5
                    break
            # 不存在，类型记录
            if type_flag == 1:
                type_flag = 4

        # 根据视频源创建一个VideoCapture对象，用于从视频源中读取帧
        # 由于ffmpeg对http和rtsp的url等待时间较长，使用另外一个线程进行处理，以便于缩减等待时间

        # 创建队列读取另一个进程的信息
        video_stream_queue = multiprocessing.Queue()
        # 创建进程，url使用video_sourse即可，队列使用创建的队列
        capture_process = Video_Capture_Process(video_sourse, video_stream_queue)
        # 运行进程
        capture_process.start()
        # 等待进程运行指定的超时时间
        capture_process.join(self.url_capture_time_out)
        # 超时时间后，查看进程情况，如果依旧运行，说明url错误，无法获得视频流，进行日志记录并返回错误
        if capture_process.is_alive():
            capture_process.terminate()
            capture_process.join()
            self.logger.log_write(f"Fail to load the network video device, the url "
                                  f"{video_sourse} caputure is timing out.",
                                  Log_Processor.ERROR)
            self.ui_value.value = 3
            return 3
        # 否则进程运行完成，获得队列结果
        # 非空时获得结果
        if not video_stream_queue.empty():
            video_stream_flag = video_stream_queue.get()
        else:
            self.logger.log_write(f"Fail to load the network video device, the url "
                                  f"{video_sourse} caputure is timing out.",
                                  Log_Processor.ERROR)
            self.ui_value.value = 3
            return 3

        # 如果结果是True，说明打开成功
        if video_stream_flag:

            video_stream = cv.VideoCapture(video_sourse, apiPreference=cv.CAP_FFMPEG)
            # 更新共享变量以说明进程启动成功
            self.ui_value.value = -9
            # 获得视频流参数，包括宽度、高度和帧率，转为整型
            real_width = int(video_stream.get(cv.CAP_PROP_FRAME_WIDTH))
            real_height = int(video_stream.get(cv.CAP_PROP_FRAME_HEIGHT))
            real_fps = int(video_stream.get(cv.CAP_PROP_FPS))

            # 如果超过了要求大小，限制其大小为720p
            # 需要注意的是，此处的限制只能对能够修改对应效果的摄像头进行处理，否则是无效的
            flag_resize = False
            # 横屏限制
            if real_width > real_height:
                if real_width > self._video_resolution[0] or real_height > self._video_resolution[1]:
                    video_stream.set(cv.CAP_PROP_FRAME_WIDTH, self._video_resolution[0])
                    video_stream.set(cv.CAP_PROP_FRAME_HEIGHT, self._video_resolution[1])
                    width = video_stream.get(cv.CAP_PROP_FRAME_WIDTH)
                    height = video_stream.get(cv.CAP_PROP_FRAME_HEIGHT)
                else:
                    width, height = real_width, real_height
                if width > self._video_resolution[0] or height > self._video_resolution[1]:
                    flag_resize = True
            # 竖屏限制
            else:
                if real_width > self._video_resolution[1] or real_height > self._video_resolution[0]:
                    video_stream.set(cv.CAP_PROP_FRAME_WIDTH, self._video_resolution[1])
                    video_stream.set(cv.CAP_PROP_FRAME_HEIGHT, self._video_resolution[0])
                    width = video_stream.get(cv.CAP_PROP_FRAME_WIDTH)
                    height = video_stream.get(cv.CAP_PROP_FRAME_HEIGHT)
                else:
                    width, height = real_width, real_height
                if width > self._video_resolution[1] or height > self._video_resolution[0]:
                    flag_resize = True
            # 帧率限制
            # fps为90000表示时钟频率，不做处理
            if real_fps != 90000 and real_fps > 30:
                video_stream.set(cv.CAP_PROP_FPS, 30)
                fps = video_stream.get(cv.CAP_PROP_FPS)
            elif real_fps == 90000:
                fps = 30
            else:
                fps = real_fps

            # 日志输出
            self.logger.log_write(f"Load the network video device " +
                                  f"{video_sourse}\n" +
                                  f"The video raal width is {real_width}, " +
                                  f"the video raal height is {real_height}, " +
                                  f"and the raal fps is {real_fps}.\n" +
                                  f"The setting video width is {width} " +
                                  f"athe setting video width is {height} " +
                                  f"The setting video width is {fps} ",
                                  Log_Processor.INFO)

            # 打开成功时，如果url不存在于配置文件中，记录该url到其中
            if type_flag == 2 or type_flag == 4:
                self.nvd_processor.add_nvd_config(video_sourse)
                self.logger.log_write(f"Append url {video_sourse} to "
                                      f"{os.path.basename(self.config_data['IP-video-device-file'])}",
                                      Log_Processor.INFO)

            # 如果需要识别视频，创建保存帧的读取队列和结果队列
            frame_queue = None
            result_queue = None
            if flag_detect:
                frame_queue = multiprocessing.Queue()
                result_queue = multiprocessing.Queue()
                # 创建进程，传入参数并运行
                video_detect_process = multiprocessing.Process(
                    target=self.video_detector.detect,
                    args=(frame_queue, result_queue, video_detect_type),
                    kwargs={"sensitivity": video_detect_sensitivity})
                video_detect_process.start()
                self.logger.log_write("Start running video detect process",
                                      Log_Processor.INFO)

            # 如果需要可视化，创建视频窗口，设置相应参数
            vis_frame_queue = None
            vis_result_queue = None
            if flag_visibility:
                vis_frame_queue = multiprocessing.Queue()
                vis_result_queue = multiprocessing.Queue()
                video_visibility_process = multiprocessing.Process(
                    target=self._network_device_visibility,
                    args=(vis_frame_queue, vis_result_queue, video_sourse, real_width, real_height))
                video_visibility_process.start()
                self.logger.log_write("Start running video visibility process",
                                      Log_Processor.INFO)

            # 如果需要保存视频，在指定目录处创建视频文件，用于写入视频帧
            video_out = None
            if flag_save:
                # 根据当前时间生成文件路径并更新历史视频处理器中的hv_dict(在函数中完成)
                try:
                    save_path = self.hs_processor.generate_video_file(
                        datetime.datetime.now().strftime(Log_Processor.strftime_all))
                # 如果目录已存在且再次创建
                except FileExistsError as e:
                    self.logger.log_write(f"Fail to create save video dir: " + e.strerror,
                                          Log_Processor.ERROR)
                    self.ui_value.value = -3
                    return -3
                # 如果路径有错误
                except OSError as e:
                    self.logger.log_write(f"Fail to create save video dir: " + e.strerror,
                                          Log_Processor.ERROR)
                    self.ui_value.value = -3
                    return -3

                # 无错误则输入视频流至文件中
                else:
                    # 声明编码保存方式
                    fourcc = cv.VideoWriter.fourcc(*"DIVX")
                    # 利用VideoWriter保存视频，文件路径为生成路径，帧率和分辨率统一为限制后的视频大小和帧率，彩色模式
                    video_out = cv.VideoWriter(save_path, fourcc, fps, (width, height), True)
                    # 如果打开成功，日志记录
                    if video_out.isOpened():
                        self.logger.log_write(f"Create save video file: {save_path}",
                                              Log_Processor.INFO)
                    # 如果打开失败，删除历史视频处理器中的hv_dict信息
                    else:
                        self.hs_processor.delete_new_video_file(save_path)
                        self.logger.log_write(f"Fail to create save video file: {save_path}",
                                              Log_Processor.ERROR)
                        self.ui_value.value = -3
                        return -3

            # 循环部分，用于读取视频
            # skip用于跳帧
            skip = 0
            while True:
                # 如果ui界面触发了关闭事件，退出进程
                if self.ui_event.is_set():
                    if flag_save:
                        video_out.release()
                    if flag_visibility:
                        vis_frame_queue.put(None)
                    video_stream.release()
                    # 由于没有终止视频帧None，手动传输结束识别进程
                    if flag_detect:
                        frame_queue.put(None)
                    break

                success = video_stream.grab()
                # 如果摄像头读取失败，日志记录，结束运行，释放视频捕捉对象，销毁窗口
                if not success:
                    self.logger.log_write(f"Fail to read the video of the network video device " +
                                          f"{video_sourse}. " +
                                          f"Please check the device.",
                                          Log_Processor.ERROR)
                    if flag_save:
                        video_out.release()

                    if flag_visibility:
                        vis_frame_queue.put(None)
                    video_stream.release()

                    # 由于没有终止视频帧None，手动传输结束识别进程
                    if flag_detect:
                        frame_queue.put(None)
                    self.ui_value.value = -2
                    return -2

                # 跳帧或者视频解码
                # 跳帧或者视频解码
                skip += 1
                skip %= 4
                if 15 <= fps < 60 and skip % 2 == 1:
                    continue
                elif fps >= 60 and skip >= 1:
                    continue
                else:
                    _, frame = video_stream.retrieve()
                # 如果视频帧分辨率大于阈值，重整为阈值
                if flag_resize == 1:
                    frame = cv.resize(frame, (self._video_resolution[0], self._video_resolution[1]),
                                      interpolation=cv.INTER_LINEAR)
                elif flag_resize == 2:
                    frame = cv.resize(frame, (self._video_resolution[1], self._video_resolution[0]),
                                      interpolation=cv.INTER_LINEAR)

                # 识别视频流的操作，放入帧并检查结果
                if flag_detect:
                    frame_queue.put(frame)
                    # 如果结果队列非空，说明出现了错误
                    if not result_queue.empty():
                        # 错误类型是一个列表，第一个元素是错误编码，第二个是各错误的置信度
                        warning_info = result_queue.get()
                        now_time = datetime.datetime.now().strftime(Log_Processor.strftime_all)
                        # 创建线程，并用报警器进行处理
                        threading.Thread(target=self.warning_processor.warning_process,
                                         args=(warning_info[0], now_time, warning_info[1], video_detect_sensitivity))
                        self.logger.log_write(f"{now_time} have exception", Log_Processor.WARNING)

                # 可见窗口时的操作
                if flag_visibility:
                    # 放入视频帧
                    vis_frame_queue.put(frame)
                    # 如果非空，说明有结果返回，说明对方终止了运行，此处也需要终止
                    if not vis_result_queue.empty():
                        # 如果返回False，说明是超时
                        if not vis_result_queue.get():
                            self.logger.log_write("video visibility process timing out.", Log_Processor.ERROR)
                        if flag_save:
                            video_out.release()
                        video_stream.release()
                        # 由于没有终止视频帧None，手动传输结束识别进程
                        if flag_detect:
                            frame_queue.put(None)
                        break

                # 保存文件时的操作
                if flag_save:
                    # 注意要重写图像大小，否则分辨率不一致时会报错
                    video_out.write(frame)

        # 打开失败则输出错误错误到日志文件中
        else:
            self.logger.log_write(f"Fail to load the network video device, use url is: " +
                                  f"{video_sourse}. The url parameter is {type_flag_dict[type_flag]}." +
                                  f" Please check the url or the config file of config "
                                  f"{os.path.basename(self.config_data['IP-video-device-file'])}",
                                  Log_Processor.ERROR)
            self.ui_value.value = -1
            return -1

        # 正常退出
        self.logger.log_write(f"Stop using the network video device " +
                              f"{video_sourse}",
                              Log_Processor.INFO)
        self.ui_value.value = 0
        return 0

    def load_history_video(self, video_strat_save_date: str,
                           video_index: int = 1,
                           flag_visibility: bool = True,
                           flag_re_detect: bool = True,
                           video_detect_sensitivity: int = 0,
                           video_detect_type: int = 1) -> int:
        """
        从历史视频保存文件夹中利用opencv库加载视频流，根据传入的视频录制日期和索引号来捕捉视频信息

        Parameters
        ----------
        video_strat_save_date : str
            要加载的历史视频的保存日期，跨日的视频以开始保存的日期为准，用于opencv库从视频源处获得视频流
            注意日期的格式为{年}分隔符{月}分隔符{日}，年一定是长为4的字符串
        video_index : int
            要加载的历史视频在保存日期的索引，用于区别单个日期保存的多个视频，默认为第一个，即索引为1
        flag_visibility : bool
            控制opencv在读取视频流时是否展示，True时展示视频，False时不展示，可用于后台处理视频
        flag_re_detect : bool
            控制历史视频是否需要进行监测，目标追踪，默认为True
        video_detect_sensitivity : int
            控制视频流在监测时的敏感度，0为低敏感度，1为高敏感度
        video_detect_type : int
            控制历史视频监测的类型，0为全部监测，1为只监测火焰，2为只监测人，3为检测异常情况

        Returns
        --------
        res : int
            返回一个整型，每个值对应一个错误类型或者正确类型
            0则说明读取、展示、识别成功
            -1则说明视频流打开失败(如视频实际是一个txt文件)
            -2则说明视频流意外关闭(如加载视频到一半被手动删除)
            1说明历史保存视频为空
            2说明要加载视频的日期无视频
            3说明索引不存在
        """

        # 检查历史保存视频是否为空
        if not self._load_flag[2]:
            self.logger.log_write("Can't load history video, the history video directory is empty.",
                                  Log_Processor.ERROR)
            self.ui_value.value = 1
            return 1

        # 获得历史视频文件及基本信息
        video_file, video_info = self.hs_processor.get_video_file(video_strat_save_date, video_index)
        # 如果日期不存在，返回2，进行日志记录
        if video_info == 2:
            self.logger.log_write(f"The {video_strat_save_date} date does not have " +
                                  f"any saved historical video files.", Log_Processor.ERROR)
            self.ui_value.value = 2
            return 2
        # 如果索引不存在，返回3，进行日志记录
        elif video_info == 3:
            self.logger.log_write(f"The {video_strat_save_date} date does not have " +
                                  f"the video file index {video_index}.", Log_Processor.ERROR)
            self.ui_value.value = 3
            return 3

        # 否则说明视频文件存在
        # 根据视频源创建一个VideoCapture对象，用于从视频源中读取帧
        video_stream = cv.VideoCapture(video_file, apiPreference=cv.CAP_ANY)

        # 判断是否打开，成功则进行下一步的处理
        if video_stream.isOpened():
            # 更新共享变量以说明进程启动成功
            self.ui_value.value = -9

            # 获得视频流参数，包括宽度、高度和帧率，转为整型
            real_width = int(video_stream.get(cv.CAP_PROP_FRAME_WIDTH))
            real_height = int(video_stream.get(cv.CAP_PROP_FRAME_HEIGHT))
            real_fps = int(video_stream.get(cv.CAP_PROP_FPS))

            # 如果超过了要求大小，限制其大小为720p
            # 横屏限制
            if real_width > real_height:
                if real_width > self._video_resolution[0] or real_height > self._video_resolution[1]:
                    width, height = self._video_resolution[0], self._video_resolution[1]
                    video_stream.set(cv.CAP_PROP_FRAME_WIDTH, width)
                    video_stream.set(cv.CAP_PROP_FRAME_HEIGHT, height)
                else:
                    width, height = real_width, real_height
            # 竖屏限制
            else:
                if real_width > self._video_resolution[1] or real_height > self._video_resolution[0]:
                    width, height = self._video_resolution[1], self._video_resolution[0]
                    video_stream.set(cv.CAP_PROP_FRAME_WIDTH, width)
                    video_stream.set(cv.CAP_PROP_FRAME_HEIGHT, height)
                else:
                    width, height = real_width, real_height
            # 帧率限制
            if real_fps > 30:
                fps = 30
                video_stream.set(cv.CAP_PROP_FPS, fps)
            else:
                fps = real_fps

            # 获得视频流总帧数和编解码格式
            video_frame_count = int(video_stream.get(cv.CAP_PROP_FRAME_COUNT))
            int_fourcc = int(video_stream.get(cv.CAP_PROP_FOURCC))
            # 编解码格式转化
            video_fourcc = ""
            for i in range(4):
                ascii_code = int((int_fourcc >> 8 * i) & 0xFF)
                video_fourcc += chr(ascii_code)
            # 计算视频时长
            if real_fps > 0:
                video_duration = video_frame_count / real_fps
            else:
                video_duration = 0
            # 获得视频大小，单位为MB
            if os.path.exists(video_file):
                video_size = os.path.getsize(video_file) / (1024 * 1024)
            else:
                video_size = 0

            ## 亮度、对比度、饱和度、色调和曝光调整
            # video_stream.set(cv.CAP_PROP_BRIGHTNESS, 1)
            # video_stream.set(cv.CAP_PROP_CONTRAST, 40)
            # video_stream.set(cv.CAP_PROP_SATURATION, 50)
            # video_stream.set(cv.CAP_PROP_HUE, 50)
            # video_stream.set(cv.CAP_PROP_EXPOSURE, 50)

            # 日志输出
            self.logger.log_write(f"Load the history video file " +
                                  f"{video_file}.\n" +
                                  f"The video raal width is {real_width}, " +
                                  f"the video raal height is {real_height}, " +
                                  f"the raal fps is {real_fps}, " +
                                  f"the video frame count is {video_frame_count}, " +
                                  f"the video duration is {video_duration:.3f}, " +
                                  f"the video size is {video_size:.3f} MB, " +
                                  f"and the video Four-Character Codes is {video_fourcc}.\n"
                                  f"The setting video width is {width} " +
                                  f"the setting video height is {height} " +
                                  f"and the setting video fps is {fps} ",
                                  Log_Processor.INFO)

            video_detect_process = None
            if flag_re_detect:
                video_detect_process = multiprocessing.Process(
                    target=self.video_detector.re_detect,
                    args=(video_file, self.ui_event, video_detect_type),
                    kwargs={"sensitivity": video_detect_sensitivity})
                video_detect_process.start()
                # 确保进程不是守护进程
                video_detect_process.daemon = False
                self.logger.log_write("Start running video detect process",
                                      Log_Processor.INFO)

            # 如果需要可视化，创建视频窗口，设置相应参数
            Window_name = ""
            if flag_visibility:
                # 窗口名，使用获得的video_info
                Window_name = f"{video_info}"
                # WINDOW_NORMAL控制窗口可以放缩，WINDOW_KEEPRATIO控制窗口缩放的过程中保持比率
                # WINDOW_GUI_EXPANDED控制使用新版本功能增强的GUI窗口
                cv.namedWindow(Window_name, flags=cv.WINDOW_NORMAL | cv.WINDOW_KEEPRATIO |
                                                  cv.WINDOW_GUI_EXPANDED)
                # 大小设置为720p的大小
                if real_width > real_height:
                    cv.resizeWindow(Window_name, 1280, 720)
                elif real_width < real_height:
                    cv.resizeWindow(Window_name, 720, 1280)
                else:
                    cv.resizeWindow(Window_name, 720, 720)

            # 循环部分，用于读取视频
            # 视频已读帧数记录，用于判断视频是否读取完毕
            frame_count = 0
            while True:
                # 如果ui界面触发了关闭事件，退出进程
                if self.ui_event.is_set():
                    if flag_visibility:
                        cv.destroyWindow(Window_name)
                    video_stream.release()
                    # 由于没有终止视频帧，直接关闭进程
                    if flag_re_detect:
                        video_detect_process.terminate()
                    break

                success, frame = video_stream.read()
                # 如果视频读取失败，判断是是否读取完毕
                if not success:
                    # 如果读取完毕，日志记录，正常退出
                    if frame_count == video_frame_count:
                        self.logger.log_write(f"All frames of the video file {video_file} " +
                                              f"has already been read.",
                                              Log_Processor.INFO)
                        if flag_visibility:
                            cv.destroyWindow(Window_name)
                        video_stream.release()
                        break
                    # 如果未完成，结束运行，日志记录，释放视频捕捉对象，销毁窗口
                    else:
                        self.logger.log_write(f"Fail to continue to read " +
                                              f"the video from the history video file {video_file}. " +
                                              f"Please check the saved file.",
                                              Log_Processor.ERROR)
                        if flag_visibility:
                            cv.destroyWindow(Window_name)
                        video_stream.release()
                        if flag_re_detect:
                            video_detect_process.terminate()
                        self.ui_value.value = -2
                        return -2

                # 成功时读取帧数+1
                frame_count += 1

                # 可见窗口时的操作
                if flag_visibility:

                    # 将当前帧在窗口中展示
                    cv.imshow(Window_name, frame)

                    # 按'q'和'ESC'键退出，释放视频捕捉对象，销毁窗口
                    # 利用waitKey控制视频播放速度
                    cv2key = cv.waitKey(int(500 / fps))
                    if cv2key & 0xFF == ord('q') or cv2key & 0xFF == 27:
                        cv.destroyWindow(Window_name)
                        video_stream.release()
                        break

                    # # 如果s键按下，则进行图片保存
                    # elif cv2key == ord('s'):
                    #     # 记录当前时间
                    #     now_time = datetime.datetime.now().strftime(Log_Processor.strftime_all)
                    #     # 写入图片 并命名图片为 图片序号.png
                    #     cv.imwrite(f"{now_time}.png", frame)

                    # 点击"x"关闭之后退出
                    if cv.getWindowProperty(Window_name, cv.WND_PROP_VISIBLE) < 1:
                        video_stream.release()
                        break

        # 打开失败则输出错误错误到日志文件中
        else:
            self.logger.log_write(f"Fail to load the history video file " +
                                  f"{video_file}.",
                                  Log_Processor.ERROR)
            self.ui_value.value = -1
            return -1

        # 正常退出
        video_detect_process.join()
        self.logger.log_write(f"Stop reading the history video file " +
                              f"{video_file}",
                              Log_Processor.INFO)
        self.ui_value.value = 0
        return 0

# 模块测试部分
if __name__ == "__main__":
    # cv支持信息查看
    # print(cv.getBuildInformation())
    # 启动opencv日志记录
    # cv.setLogLevel(cv.CAP_PROP_XI_DEBUG_LEVEL)

    # 测试加载是否成功，输出配置文件信息、视频源/设备信息
    video_process = Video_Processor()
    # print(Video_process.config_data)
    # print(Video_process.local_video_device_list)
    # print(Video_process.network_video_device_list)
    # print(Video_process.hs_processor.hv_dict)

    # 测试加载本地摄像头
    print(video_process.load_local_video_device(0, True, False, True, 2))
    # print(video_process.load_local_video_device(0, True, False))
    # print(video_process.load_local_video_device(0, True, True))

    # 测试加载网络摄像头
    # Video_process.load_network_video_device("http://10.195.154.1:8081/", True, False)
    # Video_process.load_network_video_device(3, True, False)
    # Video_process.load_network_video_device("rtsp://10.195.154.1:8554/live", True, False)
    # Video_process.load_network_video_device(4, True, True)
    # Video_process.load_network_video_device("rtsp://192.168.98.239:8554/live", True, True)

    # 测试加载历史视频文件
    # print(Video_process.load_history_video("2024-06-11", 15, True))

    # 测试识别内容
    # print(Video_process.load_local_video_device(0, True, False, True, 0))
    # print(Video_process.load_network_video_device("rtsp://10.195.146.141:8554/live",
    #                                               True, False, False, 1))
    # print(video_process.load_network_video_device("http://10.195.146.141:8081",
    #                                               True, False, True, 1))
    # print(Video_process.load_network_video_device("rtsp://10.195.146.141:8554/live",
    #                                               True, True, True, 1))
