# -*- coding: utf-8 -*-
"""
File Name: Warning_Processor.py
Author: Chai.h
Date: 2024-05-22
Version: 1.0
Description: 发出异常警报的相关处理
"""

# 引入常用库
from home_security_surveillance.Common import *
# 引入日志处理器对象
from home_security_surveillance.File_process.log import *
# 引入config模块获得默认文件位置
from home_security_surveillance.File_process.config import config_defaluts, trans_config_abspath
# 引入pygame库用于播放音频
import pygame
# 引入smtplib库用于发送邮件
import smtplib
# PIL库用于显示和加载警告信息的图像
from PIL import Image, ImageTk
# MIMEText对象用于创建 MIME（Multipurpose Internet Mail Extensions）类型的纯文本对象
from email.mime.text import MIMEText
# MIMEMultipart用于生成包含多个部分的邮件体的 MIME 对象
from email.mime.multipart import MIMEMultipart
# Header用于处理电子邮件的头信息
from email.header import Header
# parseaddr和formataddr用于处理电子邮件的地址
from email.utils import parseaddr, formataddr

__all__ = ["Warning_Processor"]

# 当前代码文件路径
_exception_config_code_file = __file__

class Warning_Processor(object):
    """
    Warning_Processor(warning_dir, user_email)
    异常警报处理器，与发出异常警报相关
    负责根据模型预测模块的结果生成警报、通知用户或相关部门，并执行相关的应急响应措施。
    该模块通过实时传递警报信息，帮助用户和管理者及时响应各类异常情况
    主要实现四个场景的警报：
    1. 火灾警报
    2. 烟雾警报
    3. 人体识别（陌生人警报）
    4. 跌倒警报

    Parameters
    ----------
    warning_dir : str
        警告日志文件存放的文件夹，默认值和_config_defaluts中exception-monitoring-directory的对应绝对路径相同

    Attributes
    ----------
     _email_senter_config_keys : List[str]
        邮件发送者配置文件可用的键值，包括email、password、name、domain和tld，是类变量
    email_smtp_address_dict : Dict[str, str]
        常用邮件服务运营商的Smtp邮箱地址和端口
    warning_code_dict : Dict[int, str]
        错误编码字典，0001对应烟雾，0010对应火焰，0100对应陌生人，1000对应跌倒异常行为
        不同的组合对应多种错误的出现，如0110代表同时出现了火焰、陌生人的错误
    warning_dir : str
        警告日志文件存放的文件夹
    warning_logger : Log_Processor
        日志处理器对象的一个实例，用于记录该类活动过程中的运行信息和警告信息
    email_senter_file : str
        邮件发送者的配置文件路径
    email_senter_data : Dict[str, str]
        邮箱发送者的email相关信息，每个元素包括email、password、username、domain、tld的键值对
    email_receiver_file : str
        邮件接收者的配置文件路径
    email_receiver_data : Dict[str, str]
        邮箱接收者的email相关信息，每个元素为邮件接收者的地址字符串
    """

    # 邮件发送者配置文件可用的键值
    _email_senter_config_keys = \
        [
            "email", "password", "username", "domain", "tld"
        ]

    # 常用邮件服务运营商的Smtp邮箱地址和端口
    email_smtp_address_dict = {"163": ("smtp.163.com", "994"),
                               "qq": ("smtp.qq.com", "587"),
                               "gmail": ("smtp.gmail.com", "587"),
                               "foxmail": ("SMTP.foxmail.com", "25"),
                               "126": ("smtp.126.com", "25"),
                               "139": ("smtp.139.com", "25")}

    # 错误编码字典
    warning_code_dict = {1: "Smoke", 2: "Fire", 4: "Stranger", 8: "Person-Falling"}

    def __init__(self,  warning_dir: str = trans_config_abspath(
                                            config_defaluts["exception-monitoring-directory"])):
        """初始化函数"""
        # 存储相关信息
        self.warning_dir = warning_dir

        # 加载日志处理器
        self.warning_logger = Log_Processor(warning_dir, "warning_processor.log", Log_Processor.INFO)

        # 保存邮件发送者的配置文件路径
        self.email_senter_file = os.path.join(self.warning_dir, "email_senter.json")
        # 加载邮件发送者的配置文件
        self.email_senter_data = self.load_email_senter_config(self.email_senter_file, True)
        self.warning_logger.log_write(f"Successfully loaded email senter file "
                                      f"{os.path.abspath(self.email_senter_file)}", Log_Processor.INFO)

        # 保存邮件接收者的配置文件路径
        self.email_receiver_file = os.path.join(self.warning_dir, "email_receiver.json")
        # 加载邮件接收者的配置文件
        self.email_receiver_data = self.load_email_receiver_config(self.email_receiver_file)
        self.warning_logger.log_write(f"Successfully loaded email receiver file "
                                      f"{os.path.abspath(self.email_senter_file)}", Log_Processor.INFO)

        # 初始化混音器模块
        pygame.mixer.init()

    # 根据错误码解析出现的错误并调用对应函数
    def warning_process(self, warning_code: int, warning_time: str, level_list: List[float], sensitivity: int=0):
        """
        错误处理的核心函数
        Parameters
        ----------
        warning_code : int
            映射所得的错误编码
        warning_time: str
            警告时间文本，说明事故发生的时间
        level_list: List[float]
            置信度列表，每个元素为对应错误的置信度
        sensitivity : int
            置信度转换为危险等级时使用的不同敏感度，0为低敏感度，1为高敏感度
        """

        # 利用与操作解析错误码，如有对应错误，进行相应报警
        # 顺序为：烟雾报警、火灾报警、陌生人报警、摔倒报警
        index = 0
        for key, value in self.warning_code_dict.items():
            if key & warning_code:
                self.trigger_warning(value, warning_time, level_list[index], sensitivity)
            index += 1

    @staticmethod
    def get_level_description(level: float, sensitivity:int = 0) -> int:
        """
        根据置信度判断危险等级，返回置信度级别描述函数
        Parameters
        ----------
        level : float
            置信度，数值在 0 ~ 1 之间
        sensitivity : int
            置信度转换为危险等级时使用的不同敏感度，0为低敏感度，1为高敏感度
        Returns
        -------
        level_description : int
            对置信度危险等级的描述，返回一个整型数，是根据置信度的大判断的危险等级：
            0~0.8表示危险性不大，危险等级为1
            0.8~0.9中等危险，又可能会发生事故，危险等级为2
            0.9~0.95大概率识别出事故，并且判断较为准确，危险等级为3
            0.95~1 极度危险状态，危险等级为4
        """
        if sensitivity == 1:
            if 0.3 <= level < 0.8:
                return 1
            elif 0.8 <= level < 0.9:
                return 2
            elif 0.9 <= level < 0.95:
                return 3
            elif 0.95 <= level <= 1:
                return 4
            else:
                return 0
        else:
            if 0.5 <= level < 0.8:
                return 1
            elif 0.8 <= level < 0.9:
                return 2
            elif 0.9 <= level < 0.95:
                return 3
            elif 0.95 <= level <= 1:
                return 4
            else:
                return 0

    def trigger_warning(self, warning_type: str, warning_time: str, level: float, sensitivity:int):
        """
        触发警报的核心处理函数
        Parameters
        ----------
        warning_type: str
            警告类型文本，根据传递的参数判断事故发生的类型，做出不同的处理
        warning_time: str
            警告时间文本，说明事故发生的时间
        level: float
            置信度，根据数值的大小判断危险等级，给出不同提示（图标显示和提示音）
            当危险等级高于等于3级时，会向户主发送邮件，通知相关情况
        sensitivity : int
            置信度转换为危险等级时使用的不同敏感度，0为低敏感度，1为高敏感度
        """
        # 置信度转危险等级
        level_description = self.get_level_description(level, sensitivity)
        # 日志记录有警告
        log_message = f"{warning_type} at {warning_time} with risk level:({level_description})"
        self.warning_logger.log_write(log_message, Log_Processor.CRITICAL)

        # 危险等级超过3就发送邮件
        if level_description >= 3:
            self.send_email_notification(warning_type, warning_time, level_description)
            log_message += " Start to sent Message!"
            self.warning_logger.log_write(log_message, Log_Processor.INFO)

        # 警告播放
        self._play_audio(level_description)
        # 桌面跳出警报窗口
        self.show_custom_warning_dialog(warning_type, warning_time, level_description)

    def _play_audio(self, level_description: int):
        """
        音乐播放函数
        Parameters
        ----------
        level_description : int
            对置信度危险等级的描述，对应1-4级别
        """

        # 播放存储路径的音乐
        music_file = os.path.join(self.warning_dir,
                                  f"warning_audio/{level_description}.mp3")
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play()
        self.warning_logger.log_write(f"Successfully played mixer music file "
                                      f"{music_file}", Log_Processor.INFO)

    def show_custom_warning_dialog(self, warning_type: str, warning_time: str, level_description: int):
        """
        桌面跳出警报窗口函数
        Parameters
        ----------
        warning_type : str
            警告类型文本
        warning_time : str
            警告时间文本
        level_description : int
            置信度危险等级
        """
        root = tk.Tk()
        root.title("Warning")

        # 设置窗口大小和位置
        window_width = 500
        window_height = 200
        # 自动调整宽度高度以适应窗口
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        # 居中位置计算
        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)
        # 使窗口居中
        root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")

        # 显示警报信息
        # 设置字体和大小
        font_style = ("Helvetica", 15)
        # 警告文本
        label_text = f"{warning_type} detected at {warning_time}\n" \
                     f"Risk level: {level_description}"
        label = ttk.Label(root, text=label_text, padding=(20, 10), font=font_style)
        # 在父容器中自动排列和管理文本的位置和大小
        label.pack()

        # 创建图标框架
        icon_frame = ttk.Frame(root)
        # 设置图标框架与上方组件的间距
        icon_frame.pack(pady=(10, 0))

        # 加载和显示警告类型图片
        warning_image_path = os.path.join(self.warning_dir, f"warning_png/{warning_type}.png")
        # 打开图像
        warning_image = Image.open(warning_image_path)
        # 图像缩放到指定的大小
        warning_image = warning_image.resize((50, 50), resample=Image.Resampling.LANCZOS)
        # 将缩放后图像转为PhotoImage对象
        warning_photo = ImageTk.PhotoImage(warning_image)
        # 图像加载到窗口
        warning_label = ttk.Label(icon_frame, image=warning_photo)
        # 保持对图片的引用
        warning_label.image = warning_photo
        # 设置图标之间的水平间距
        warning_label.pack(side=tk.LEFT, padx=(0, 10))

        # 加载和显示危险等级图标
        risk_image_path = os.path.join(self.warning_dir, f"warning_png/{level_description}.png")
        risk_image = Image.open(risk_image_path)
        risk_image = risk_image.resize((50, 50), Image.Resampling.LANCZOS)
        risk_photo = ImageTk.PhotoImage(risk_image)
        risk_label = ttk.Label(icon_frame, image=risk_photo)
        # 保持对图片的引用
        risk_label.image = risk_photo
        risk_label.pack(side=tk.LEFT)

        # OK 按钮
        ok_button = ttk.Button(root, text="OK", command=root.destroy)
        ok_button.pack(pady=10)
        root.mainloop()

    def _write_email_senter_config(self, config_data: Dict[str, str] = {}):
        """
        将传入的邮件发送者的数据写入配置文件，视为内部函数，不提供外部接口
        Parameters
        ----------
        config_data : Dict[str, str]
            传入要修改的数据，默认为空
        """

        # 写入config_data
        if config_data:
            # 打开文件，获得数据
            with open(self.email_senter_file, 'r') as file:
                data = json.load(file)
                # 如果只有一个字典，转为列表
                if isinstance(data, dict):
                    data = [data]
                # 去除没有email的字典和email为空的字典
                data = [i for i in data
                        if "email" in i.keys() and i["email"] != ""]
                # 如果文件有邮箱地址且传入的修改邮件地址与文件第一个地址相同，则为修改
                if len(data) != 0 and data[0]["email"] == config_data["email"]:
                    data[0] = config_data
                # 否则为添加，且更新到第一个位置
                else:
                    # 先删除和该email相同的data内容
                    # 反向遍历避免引发索引错误或跳过元素
                    for i in range(len(data) - 1, -1, -1):
                        if data[i]["email"] == config_data["email"]:
                            del data[i]
                    data.insert(0, config_data)
            # 写入修改后的data
            with open(self.email_senter_file, 'w', encoding='utf-8') as file:
                json.dump(data, file,
                          skipkeys=False, check_circular=True, allow_nan=True, sort_keys=False,
                          ensure_ascii=False, separators=(',', ' : '), indent=2)

    def _write_email_receiver_config(self, config_data: List[str] = []):
        """
        将传入的邮件接收者的数据写入配置文件，视为内部函数，不提供外部接口
        Parameters
        ----------
        config_data : List[str]
            传入要修改的数据，默认为空
        """

        # 写入config_data
        with open(self.email_receiver_file, 'w', encoding='utf-8') as file:
            json.dump(config_data, file,
                skipkeys=False, check_circular=True, allow_nan=True, sort_keys=False,
                ensure_ascii=False, separators=(',', ' : '), indent=2)

    def load_email_senter_config(self, email_senter: str, re_parse: bool = True) \
            -> Dict[str, str]:
        """
        加载邮件发送者配置文件为对应的数据结构
        Parameters
        ----------
        email_senter : str
            要加载的邮件发送者配置文件的路径
        re_parse : bool
            是否重新解析email的内容，默认为True
        Returns
        -------
        email_senter_data : Dict[str, str]
            邮件发送者文件中json列表的第一个字典的解析所得数据，每个元素对应一个存储邮件发送者相关信息的字符串
        """
        # 打开文件进行加载，加载的错误在调用处进行处理
        with open(email_senter, 'r', encoding='utf-8') as file:
            # 加载邮件发送者配置文件内容
            email_senter_all_data = json.load(file)
            # 如果只有一个字典，转为列表
            if isinstance(email_senter_all_data, dict):
                email_senter_all_data = [email_senter_all_data]
            # 去除没有email的字典或者email为空的字典
            email_senter_all_data = [i for i in email_senter_all_data
                                     if "email" in i.keys() and i["email"] != ""]
            # 无内容返回空字典
            if len(email_senter_all_data) == 0:
                return {}
            # 只保留第一个列表的内容
            email_senter_data = email_senter_all_data[0]
            # 格式化email
            email_senter_data["email"] = self._format_addr(email_senter_data["email"])
            # 对email的内容进行直接解析
            email_parts = self.slice_email(email=email_senter_data["email"])

            # 如果设置了重新解析，赋值
            if re_parse:
                email_senter_data["username"] = email_parts["username"]
                email_senter_data["domain"] = email_parts["domain"]
                email_senter_data["tld"] = email_parts["tld"]
            # 如果未设置重新解析，对不存在的值赋值
            else:
                if "username" not in email_senter_data.keys():
                    email_senter_data["username"] = email_parts["username"]
                if "domain" not in email_senter_data.keys():
                    email_senter_data["domain"] = email_parts["domain"]
                if "tld" not in email_senter_data.keys():
                    email_senter_data["tld"] = email_parts["tld"]

        # 如果有读取结果，重新写入
        if email_senter_data:
            self._write_email_senter_config(email_senter_data)
        return email_senter_data

    def load_email_receiver_config(self, email_receiver: str) -> List[str]:
        """
        加载邮件发送者配置文件为对应的数据结构
        Parameters
        ----------
        email_receiver : str
            要加载的邮件接收者配置文件的路径
        Returns
        -------
        email_receiver_data : List[str]
            邮件接收者文件解析所得数据，是一个字符串列表，每个元素对应一个邮件接收者地址字符串
        """
        # 打开文件进行加载，加载的错误在调用处进行处理
        with open(email_receiver, 'r', encoding='utf-8') as file:
            # 加载邮件发送者配置文件内容
            email_receiver_data = json.load(file)
            # 格式化并删除错误邮件地址
            email_receiver_data = [i for i in email_receiver_data
                                   if self.slice_email(self._format_addr(i))]
        # 返回结果
        return email_receiver_data

    def append_email_senter(self, email_senter_address: str, email_senter_password) -> bool:
        """
        添加邮件发送者函数，作为最新值使用
        Parameters
        ----------
        email_senter_address:  str
            邮件发送者邮件地址
        email_senter_password : str
            邮件发送者邮件密码
        Returns
        -------
        flag : bool
            是否添加成功
        """
        new_email_senter_data = {}
        # 格式化邮件地址
        email_senter_address = self._format_addr(email_senter_address)
        # 解析邮件
        email_senter_parts = self.slice_email(email_senter_address)
        # 如果符合邮件格式，添加邮件地址并写入文件，更新
        if email_senter_parts:
            new_email_senter_data["email"] = email_senter_address
            new_email_senter_data["password"] = email_senter_password
            new_email_senter_data["username"] = email_senter_parts["username"]
            new_email_senter_data["domain"] = email_senter_parts["domain"]
            new_email_senter_data["tld"] = email_senter_parts["tld"]
            self.email_senter_data = new_email_senter_data
            self._write_email_senter_config(new_email_senter_data)
            self.warning_logger.log_write(f"Successfully appended the email senter "
                                          f"{new_email_senter_data}", Log_Processor.INFO)
            return True
        else:
            self.warning_logger.log_write(f"Failed to append the email senter "
                                          f"{email_senter_address}, please check the address",
                                          Log_Processor.WARNING)
            return False

    def append_email_receiver(self, email_receiver_address: str) -> bool:
        """
        添加邮件接收者函数
        Parameters
        ----------
        email_receiver_address:  str
            邮件接收者函数地址
        Returns
        -------
        flag : bool
            是否添加成功
        """
        # 格式化邮件地址
        email_receiver_address = self._format_addr(email_receiver_address)
        # 如果符合邮件格式
        if self.slice_email(email_receiver_address):
            # 如果未添加过该地址，添加邮件地址并写入文件
            for i in self.email_receiver_data:
                if i == email_receiver_address:
                    self.warning_logger.log_write(f"The the email receiver has existed"
                                                  f"{email_receiver_address}", Log_Processor.INFO)
                    return True
            self.email_receiver_data.append(email_receiver_address)
            self._write_email_receiver_config(self.email_receiver_data)
            self.warning_logger.log_write(f"Successfully appended the email receiver "
                                          f"{email_receiver_address}", Log_Processor.INFO)
            return True
        else:
            self.warning_logger.log_write(f"Failed to append the email receiver "
                                          f"{email_receiver_address}, please check the address",
                                          Log_Processor.WARNING)
            return False

    def delete_email_receiver(self,email_receiver_address: str) -> bool:
        """
        删除邮件接收者函数
        Parameters
        ----------
        email_receiver_address:  str
            邮件接收者函数地址
        Returns
        -------
        flag : bool
            是否添加成功
        """
        # 格式化邮件地址
        email_receiver_address = self._format_addr(email_receiver_address)
        # 如果符合邮件格式
        if self.slice_email(email_receiver_address):
            # 如果未添加过该地址，添加邮件地址并写入文件
            for i in range(len(self.email_receiver_data) - 1, -1, -1):
                if self.email_receiver_data[i] == email_receiver_address:
                    del self.email_receiver_data[i]
                    self._write_email_receiver_config(self.email_receiver_data)
                    self.warning_logger.log_write(f"Successfully deleted the email receiver "
                                                  f"{email_receiver_address}", Log_Processor.INFO)
                    return True

        self.warning_logger.log_write(f"Failed to deleted the email receiver "
                                      f"{email_receiver_address}, please check the address",
                                      Log_Processor.WARNING)
        return False

    @staticmethod
    def _format_addr(email: str) -> str:
        """
        处理包含非ASCII字符的电子邮件地址
        Parameters
        ----------
        email: str
            传入的电子邮件地址

        Returns
        -------
        format_email_address : str
            格式化后的电子邮件地址
        """

        # 解析电子邮件地址，获得邮件姓名和地址
        realname, email_address = parseaddr(email)
        # 格式化电子邮件地址再返回
        return formataddr((Header(realname, 'utf-8').encode(), email_address))

    @staticmethod
    def slice_email(email: str) -> Dict[str, str]:
        """
        邮件地址切片函数
        Parameters
        ----------
        email : str
            传入的电子邮件地址

        Returns
        -------
        email_parts : Dict[str, str]
            邮件的各个部分，username属性对应邮件名，domain属性对应域名，tld属性对应顶级域名
        """

        # 邮件信息解析格式
        email_pattern = r'([^@]+)@([^\.]+)\.([^.]+)'
        # 正则表达式邮件信息解析
        match = re.match(email_pattern, email)
        parts = {}
        # 记录解析结果
        if match:
            parts['username'] = match.group(1)
            parts['domain'] = match.group(2)
            parts['tld'] = match.group(3)
        return parts

    def send_email_notification(self, warning_type: str, warning_time: str, level_description: int):
        """
        发送邮件通知用户发生了相应的紧急事故函数
        Parameters
        ----------
        warning_type : str
            警告类型文本
        warning_time : str
            警告时间文本
        level_description : int
            置信度危险等级
        """

        # 邮件标题
        email_subject = f"来自家庭安全监控系统的警告！！！"
        # 邮件内容
        body = f"""
        检测到事故: {warning_type}
        发生时间: {warning_time}
        危险等级: {level_description}级
        """
        # 本来还想可以加一个 查看视频：url    这里不知道怎么传参了

        # email结构设置
        eamil_message = MIMEMultipart()
        # 寄件人设置
        eamil_message['From'] = self.email_senter_data["email"]
        # 收件人设置，是一个列表
        eamil_message['To'] = Header(",".join(self.email_receiver_data))
        # 邮件标题设置
        eamil_message['Subject'] = Header(email_subject, 'utf-8')
        # 添加正文内容
        eamil_message.attach(MIMEText(body, 'plain'))

        # 发送邮件
        try:
            # 先获得对应的邮件域名的对应发送地址和端口
            smtp_address, smtp_port = self.email_smtp_address_dict[self.email_senter_data["domain"]]
            # 连接到SMTP服务器，使用SSL方式
            with smtplib.SMTP_SSL(smtp_address, smtp_port) as server:
                # 发送SMTP的“HELLO”消息
                server.ehlo()
                # 3. 登陆到SMTP服务器
                server.login(self.email_senter_data["email"], self.email_senter_data["password"])
                # 4. 发送电子邮件
                server.sendmail(self.email_senter_data["email"], self.email_receiver_data,
                                eamil_message.as_string())
                # 5. 从服务器断开
                server.quit()
            self.warning_logger.log_write(f"Email sent to {','.join(self.email_receiver_data)} "
                                          f"for {warning_type}", Log_Processor.INFO)
        except Exception as e:
            self.warning_logger.log_write(f"Failed to send email: {str(e)}", Log_Processor.ERROR)


# 模块测试部分
if __name__ == "__main__":
    # 初始化对象
    warning_processor = Warning_Processor()

    # # 添加邮件发送者并检验添加结果
    # warning_processor.append_email_senter("2560663471@qq.com", "mwgzhmvcvjktebce")
    # print(warning_processor.email_senter_data)
    # warning_processor.append_email_senter("xiaohei07zhzhh@163.com", "MLTMTIOQITHANNNG")
    # print(warning_processor.email_senter_data)
    #
    # # 添加邮件接收者并检验添加结果
    # warning_processor.append_email_receiver("2193706008@qq.com")
    # print(warning_processor.email_receiver_data)
    # warning_processor.append_email_receiver("2560663471@qq.com")
    # print(warning_processor.email_receiver_data)
    # warning_processor.append_email_receiver("xiaohei07zhzhh@163.com")
    # print(warning_processor.email_receiver_data)
    # warning_processor.append_email_receiver("lazy07xiaohei@163.com")
    # print(warning_processor.email_receiver_data)

    # # 删除邮件接收者并检验添加结果
    # warning_processor.delete_email_receiver("2193706008@qq.com")
    # print(warning_processor.email_receiver_data)
    # warning_processor.delete_email_receiver("xiaohei07zhzhh@163.com")
    # print(warning_processor.email_receiver_data)
    # warning_processor.delete_email_receiver("lazy07xiaohei@163.com")
    # print(warning_processor.email_receiver_data)

    # # 邮件发送测试
    # warning_processor.send_email_notification("Fire", "2024-06-12 12:00:00", 3)

    # 测试警告功能
    # warning_processor.warning_process(1, "2024-06-12 12:00:00", 0.8)
    # warning_processor.warning_process(2, "2024-06-12 12:00:00", 0.85)
    # warning_processor.warning_process(4, "2024-06-12 12:00:00", 0.9)
    # warning_processor.warning_process(9, "2024-06-12 12:00:00", 0.95)
    # warning_processor.warning_process(15, "2024-06-12 12:00:00", 0.8)

    # # 单独的连接测试
    # # 1. 连接到SMTP服务器
    # smtpObj = smtplib.SMTP('smtp.qq.com', 587)
    #
    # # 2. 发送SMTP的“HELLO”消息
    # smtpObj.ehlo()
    #
    # # 3. 开始TLS加密
    # smtpObj.starttls()
    #
    # # 4. 登陆到SMTP服务器
    # smtpObj.login('2560663471@qq.com', 'mwgzhmvcvjktebce')
    #
    # # 5. 发送电子邮件
    # from_addr = '2560663471@qq.com'  # 发件人
    # to_addr = '2560663471@qq.com'  # 收件人
    #
    # message = MIMEText('Happy new year!', 'plain', 'utf-8')  # 正文
    # message['From'] = Warning_Processor._format_addr('Sam <%s>' % from_addr)  # 发件人
    # message['To'] = Warning_Processor._format_addr('Python lover <%s>' % to_addr)  # 收件人
    #
    # subject = 'Python SMTP 邮件测试'
    # # 主题
    # message['Subject'] = Header(subject, 'utf-8')
    #
    # smtpObj.sendmail(from_addr, [to_addr], message.as_string())
    #
    # # 6. 从服务器断开
    # smtpObj.quit()
    #
    # print("Done!")
