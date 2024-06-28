# -*- coding: utf-8 -*-
"""
File Name: ui.py
Author: Captain
Date: 2024-06-06
Version: 1.5
Description: 提供简洁的图形化界面
"""


# 引入常用库
from home_security_surveillance.Common import *
# 引入Warning_Processor库
from home_security_surveillance.Exception_process.Warning_Processor import *
# 引入video_processor库
from home_security_surveillance.Video_process import *
# 引入Log_Processor库和History_Video_Processor库
from home_security_surveillance.File_process import Log_Processor, History_Video_Processor
# 引入messagebox类
from tkinter import messagebox
# 引入psutil库
import psutil
# 引入sys库
import sys


__all__ = ["VideoMonitorApp"]

class VideoMonitorApp:
    """
    VideoMonitorApp(root)

    根据用户的操作完成相应的家庭监控设置和分析，是家庭监控系统的用户交互和任务分发部分

    Parameters
    ----------
    root : tk.TK
        用于创建和用户进行交互的主窗口

    Attributes
    ----------
    root : tk.TK
        和用户进行交互的主窗口，在上面可以定义各种控件
    video_processor : Video_Processor
        视频流处理器的一个实例，此处是一个静态实例，不执行任务，主要用于获得各种视频设备和视频文件信息
    process_type : int
        执行任务的进程对应的进程类型，0表示没有执行任务的进程，1表示执行加载和处理本地历史视频任务的进程，
        2表示执行加载和处理本地视频设备任务的进程，3表示执行加载和处理网络视频设备任务的进程
    processes : multiprocessing.Process
        存储multiprocessing进程对象的成员变量，是执行任务进程的句柄
    shared_value : multiprocessing.Value
        为其他进程所共享的共享内存对象，创建为一个整型，默认为-10，用于保存其他进程的返回值
        根据不为-10的返回值可以确定错误情况
    shared_event : multiprocessing.Event
        进程事件通信对象，用于通知执行任务进程是否停止，每次创建执行任务进程时刷新

    Notes
    -----
    在该类中加载了静态视频处理对象，每次创建进程执行任务时需要加载一个动态的视频处理对象，此时不会产生IO冲突
    类内创建了各种控件，此处不再一一说明

    Examples
    --------
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("家庭视频监控软件")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # 类内的默认处理器对象，用于在Video_Processor中的获得相关信息
        self.video_processor = Video_Processor()
        # 进程类型和进程对象
        self.process_type = 0
        self.processes = None
        # 创建共享变量和进程事件
        self.shared_value = multiprocessing.Value('i', -10)
        self.shared_event = multiprocessing.Event()
        self.center_window(self.root, 550, 380)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)
        root.grid_rowconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        root.grid_rowconfigure(2, weight=1)
        root.grid_rowconfigure(3, weight=1)
        root.grid_rowconfigure(4, weight=1)
        root.grid_rowconfigure(5, weight=1)
        style = ttk.Style()
        self.label_font = ("微软雅黑", 12)
        style.configure("TLabel", font=self.label_font)
        style.configure("TButton", font=self.label_font)
        style.configure("TCheckbutton", font=self.label_font)
        style.configure("TRadiobutton", font=self.label_font)
        style.configure("TEntry", font=self.label_font)
        style.configure("TMenubutton", font=self.label_font)
        self.create_widgets()

    @staticmethod
    def center_window(window: Union[tk.Toplevel, tk.Tk], width: int, height: int):
        """
        窗口居中设置函数，静态方法
        Parameters
        ----------
        window : Union[tk.Toplevel, tk.TK]
            要设置居中的窗口对象，可以是主窗口或者其他顶层窗口
        width : int
            窗口的宽度
        height : int
            窗口的高度
        """
        # 获取屏幕宽度和高度
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        # 计算窗口左上角坐标
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        # 设置窗口大小和位置
        window.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """添加窗口组件函数，用于创建大部分主窗口上的组件"""
        # 选择视频来源
        self.source_label = ttk.Label(self.root, text="选择视频来源:")
        self.source_label.grid(row=0, column=0, padx=20, pady=10)
        self.source_var = tk.StringVar()
        self.source_var.set("本地摄像设备")
        self.source_options = ["", "本地历史视频", "本地摄像设备", "网络摄像设备"]
        self.source_menu = ttk.OptionMenu(self.root, self.source_var, *self.source_options, command=self.confirm_source)
        # self.source_menu.configure(font=label_font)
        self.source_menu.grid(row=0, column=1, pady=10, columnspan=2, sticky='W')
        self.source_menu['menu'].config(font=self.label_font)
        self.date_url = ''

        # 选择可用设备或视频
        self.video_device_label = ttk.Label(self.root, text="选择可用设备:")
        self.video_device_label.grid(row=1, column=0, padx=20, pady=10)
        self.video_device_var = tk.StringVar()
        if self.video_processor.local_video_device_list:
            self.video_device_var.set(self.video_processor.local_video_device_list[0][1])
        else:
            self.video_device_var.set('')
        self.video_device_options = [''] + list(value for _, value in
                                                self.video_processor.local_video_device_list)
        self.video_device_menu = ttk.OptionMenu(self.root, self.video_device_var, *self.video_device_options)
        self.video_device_menu.grid(row=1, column=1, pady=10, columnspan=2, sticky='W')
        self.video_device_menu['menu'].config(font=self.label_font)

        # 选择处理方式
        self.process_mode_label = ttk.Label(self.root, text="选择处理方式:")
        self.process_mode_label.grid(row=2, column=0, padx=20, pady=10)
        self.bottom1 = tk.Frame(self.root)
        self.bottom1.grid(row=2, column=1, columnspan=2, sticky='W')
        c1 = tk.Frame(self.bottom1)
        c1.pack(fill="x")
        self.visibility_var = tk.BooleanVar()
        self.visibility_check = ttk.Checkbutton(c1, text="可视化", variable=self.visibility_var,
                                                command=self.check_start)
        self.visibility_var.set(True)
        self.visibility_check.grid(row=0, column=0, padx=10, pady=10)

        self.detect_var = tk.BooleanVar()
        self.detect_check = ttk.Checkbutton(c1, text="检测", variable=self.detect_var,
                                            command=self.check_start)
        self.detect_check.grid(row=0, column=1, padx=40, pady=10)

        self.save_var = tk.BooleanVar()
        self.save_check = ttk.Checkbutton(c1, text="录制", variable=self.save_var,
                                          command=self.check_start)
        self.save_check.grid(row=0, column=2, padx=10, pady=10)

        # 选择检测类型
        self.detect_type_label = ttk.Label(self.root, text="选择检测类型:")
        self.detect_type_label.grid(row=3, column=0, pady=10)
        self.detect_type_var = tk.StringVar()
        self.detect_type_var.set("全部")
        self.detect_type_options = ["", "全部", "火焰", "人员", "异常情况"]
        self.detect_type_menu = ttk.OptionMenu(self.root, self.detect_type_var, *self.detect_type_options)
        self.detect_type_menu.grid(row=3, column=1, pady=10, sticky='W')

        # 检测敏感度
        self.sensitivity_label = ttk.Label(self.root, text="检测敏感度:")
        self.sensitivity_label.grid(row=4, column=0, pady=10)
        self.bottom2 = tk.Frame(self.root)
        self.bottom2.grid(row=4, column=1, sticky='W')
        c2 = tk.Frame(self.bottom2)
        c2.pack(fill="x")
        self.sensitivity_var = tk.IntVar()
        self.sensitivity_var.set(1)
        self.sensitivity_low = ttk.Radiobutton(c2, text="低", variable=self.sensitivity_var, value=0)
        self.sensitivity_low.grid(row=0, column=0, padx=10, pady=10)
        self.sensitivity_high = ttk.Radiobutton(c2, text="高", variable=self.sensitivity_var, value=1)
        self.sensitivity_high.grid(row=0, column=1, padx=50, pady=10)

        # 开始和停止按钮
        self.bottom3 = tk.Frame(self.root)
        self.bottom3.grid(row=5, column=0, pady=10, columnspan=3)
        c3 = tk.Frame(self.bottom3)
        c3.pack(fill="x")
        c3.columnconfigure(0, weight=1)
        c3.columnconfigure(1, weight=1)
        self.start_button = ttk.Button(c3, text="开始", command=self.start_monitoring)
        self.stop_button = ttk.Button(c3, text="停止", command=self.stop_monitoring)
        self.email_button = ttk.Button(c3, text="邮件管理", command=self.email_manage)
        self.start_button.grid(row=0, column=0, padx=30, pady=10)
        self.stop_button.grid(row=0, column=1, padx=30, pady=10)
        self.email_button.grid(row=0, column=2, padx=30, pady=10)

        # 测试按钮
        # self.start_button = ttk.Button(self.root, text="测试", command=self.start_test)
        # self.start_button.grid(row=6, column=0, pady=10)

        # 用于确认视频来源

    def check_start(self):
        """
        根据三个Checkbutton对应的Var的状态，检查开始按钮是否可以点击
        """
        if not self.visibility_var.get() and not self.detect_var.get() and not self.save_var.get():
            self.start_button.config(state=tk.DISABLED)  # 将"开始"按钮设为不可用
        else:
            self.start_button.config(state=tk.NORMAL)  # 将"开始"按钮设为可用

    def confirm_source(self, value: str):
        """
        确定资源信息函数，用于选择视频设备类型时的处理，与主窗口选择视频类型的操作列表绑定
        此处在有需要时会在主窗口上创建子窗口完成相应处理
        Parameters
        ----------
        value : str
            读取到的用户选择的视频设备类型字符串名陈
        """
        if str(self.start_button['state']) == tk.DISABLED:
            self.start_button.config(state=tk.NORMAL)  # 将"开始"按钮设为可用
        # 根据不同选择进行组件的不同处理
        if value == "本地摄像设备":
            if self.video_processor.local_video_device_list:
                self.video_device_var.set(self.video_processor.local_video_device_list[0][1])
            else:
                self.video_device_var.set('')

            self.video_device_options = [''] + list(value for _, value in
                                                    self.video_processor.local_video_device_list)
            self.video_device_menu.destroy()
            self.video_device_menu = ttk.OptionMenu(self.root, self.video_device_var, *self.video_device_options)
            self.video_device_menu.grid(row=1, column=1, pady=10, columnspan=2, sticky='W')
            self.video_device_menu['menu'].config(font=self.label_font)
            self.video_device_label.destroy()
            self.video_device_label = ttk.Label(self.root, text="选择可用设备:")
            self.video_device_label.grid(row=1, column=0, pady=10)
            self.save_check.grid()
            return

        input_window = tk.Toplevel(self.root)
        self.root.attributes('-disabled', True)
        input_window.protocol('WM_DELETE_WINDOW', lambda: cancel())  # 将关闭按钮与取消函数关联
        input_var = tk.StringVar()

        # 子函数，用于选择url地址
        def choose_address(sub_value):
            input_var.set(sub_value)

        input_entry = ttk.Entry(input_window, font=self.label_font, textvariable=input_var, width=30)
        if value == "本地历史视频":
            input_entry.config(foreground='grey')
            input_entry.insert(0, '示例: 1949-10-01')
            input_window.title("输入视频日期")
            self.center_window(input_window, 410, 125)
            ttk.Label(input_window, text="输入视频日期:").grid(row=0, column=0, padx=5, pady=20)

            def on_entry_click(event):
                if input_entry.get() == '示例: 1949-10-01':
                    input_entry.delete(0, tk.END)  # 清空当前内容
                    input_entry.config(foreground='black')  # 恢复正常文本颜色

            input_entry.bind('<FocusIn>', on_entry_click)
            self.video_device_label.destroy()
            self.video_device_label = ttk.Label(self.root, text="选择可用视频:")
            self.video_device_label.grid(row=1, column=0, pady=10)

        elif value == "网络摄像设备":
            self.save_check.grid()
            input_window.title("输入摄像头地址")
            self.center_window(input_window, 410, 170)
            ttk.Label(input_window, text="输入设备地址:").grid(row=0, column=0, padx=5, pady=20)
            address_label = ttk.Label(input_window, text="选择已有地址:")
            address_label.grid(row=1, column=0, padx=5, pady=10)
            if self.video_processor.nvd_processor.nvd_config_data:
                url_list = [list(d.values())[0] for d in self.video_processor.nvd_processor.nvd_config_data]
            else:
                url_list = [""]
            address_var = tk.StringVar()
            address_var.set(url_list[0])
            address_options = [''] + url_list
            address_menu = ttk.OptionMenu(input_window, address_var, *address_options, command=choose_address)
            address_menu.grid(row=1, column=1, pady=10, sticky='W')
            address_menu['menu'].config(font=self.label_font)
            self.video_device_label.destroy()
            self.video_device_label = ttk.Label(self.root, text="选择可用设备:")
            self.video_device_label.grid(row=1, column=0, pady=10)

        input_entry.grid(row=0, column=1, padx=5, pady=10)

        def submit():
            """提交子函数，与子窗口的“提交”按钮绑定，规定了子窗口时的交互行为"""
            # 获得提交信息，根据信息进行不同的处理
            input_var.get()
            self.date_url = input_entry.get()

            if value == "本地历史视频":
                self.date_url = History_Video_Processor.format_date(
                    History_Video_Processor.parse_date(input_entry.get(), "-"))
                try:
                    video_list = [d[1] for d in self.video_processor.hs_processor.hv_dict[self.date_url].values()]
                except KeyError:
                    messagebox.showwarning("提示", "日期格式错误或该日期下无视频\n请重新输入日期")
                    self.video_device_var.set('')  # 取消已选项目
                    self.video_device_options.clear()  # 删除可选项目
                    self.video_device_menu.destroy()
                    self.video_device_menu = ttk.OptionMenu(self.root, self.video_device_var,
                                                            *self.video_device_options)
                    self.video_device_menu.grid(row=1, column=1, pady=10, columnspan=2, sticky='W')
                    self.video_device_menu['menu'].config(font=self.label_font)

                else:
                    self.video_device_var.set(video_list[0])
                    self.video_device_options = [''] + video_list
                self.save_check.grid_remove()
                self.video_device_menu.destroy()
                self.video_device_menu = ttk.OptionMenu(self.root, self.video_device_var, *self.video_device_options)
                self.video_device_menu.grid(row=1, column=1, pady=10, columnspan=2, sticky='W')
                self.video_device_menu['menu'].config(font=self.label_font)

            elif value == "网络摄像设备":
                self.save_check.grid()
                self.video_device_var.set(self.date_url)
                self.video_device_options = ['', self.date_url]
                self.video_device_menu.destroy()
                self.video_device_menu = ttk.OptionMenu(self.root, self.video_device_var, *self.video_device_options)
                self.video_device_menu.grid(row=1, column=1, pady=10, columnspan=2, sticky='W')
                self.video_device_menu['menu'].config(font=self.label_font)
            self.video_device_menu = ttk.OptionMenu(self.root, self.video_device_var, *self.video_device_options)
            self.root.attributes('-disabled', False)  # 将主窗口设为可用
            input_window.destroy()  # 关闭窗口
            return

        def cancel():
            """取消子函数，与子窗口的"取消"按钮绑定，规定了子窗口时的交互行为"""
            if value == "本地历史视频":
                self.save_check.grid_remove()
                self.start_button.config(state=tk.DISABLED)  # 将"开始"按钮设为不可用
            elif value == "网络摄像设备":
                self.start_button.config(state=tk.DISABLED)  # 将"开始"按钮设为不可用
            self.root.attributes('-disabled', False)  # 将主窗口设为可用
            self.video_device_var.set('')  # 取消已选项目
            self.video_device_options.clear()  # 删除可选项目
            self.video_device_menu.destroy()
            self.video_device_menu = ttk.OptionMenu(self.root, self.video_device_var, *self.video_device_options)
            self.video_device_menu.grid(row=1, column=1, pady=10, columnspan=2, sticky='W')
            self.video_device_menu['menu'].config(font=self.label_font)
            input_window.destroy()  # 关闭窗口
            return

        # 创建子窗口时使用
        self.bottom = tk.Frame(input_window)
        self.bottom.grid(row=2, column=0, columnspan=2)
        c = tk.Frame(self.bottom)
        c.pack(fill="x")
        c.columnconfigure(0, weight=1)
        c.columnconfigure(1, weight=1)
        submit_button = ttk.Button(c, text="提交", command=submit)
        cancel_button = ttk.Button(c, text="取消", command=cancel)
        submit_button.grid(row=0, column=0, padx=30, pady=10)
        cancel_button.grid(row=0, column=1, padx=30, pady=10)
        self.video_processor.logger.log_write(f"Finish setting {value}", Log_Processor.INFO)

    def start_monitoring(self):
        """
        与主窗口的“开始”按钮绑定，用于创建执行任务的子进程
        与其他模块进行交互，是连接前后端的关键函数
        """
        self.start_button.config(state=tk.DISABLED)  # 将"开始"按钮设为不可用
        self.email_button.config(state=tk.DISABLED)  # 将"邮件管理"按钮设为不可用
        type_dict = {'全部': 0, '火焰': 1, '人员': 2, '异常情况': 3}
        source = self.source_var.get()
        # 重建共享变量和进程事件
        self.shared_value.value = -10
        self.shared_event = multiprocessing.Event()

        # 根据用户选择的不同资源信息进行进程创建和任务执行
        if source == "本地历史视频":
            self.process_type = 1
            video_index_dict = {val[1]: key for key, val in
                                self.video_processor.hs_processor.hv_dict[self.date_url].items()}
            self.processes = multiprocessing.Process(
                target=self.history_video_process_workder,
                args=(),
                kwargs={
                    "shared_value": self.shared_value,
                    "shared_event": self.shared_event,
                    "video_strat_save_date": self.date_url,
                    "video_index": video_index_dict[self.video_device_var.get()],
                    "flag_visibility": self.visibility_var.get(),
                    "flag_re_detect": self.detect_var.get(),
                    "video_detect_sensitivity": self.sensitivity_var.get(),
                    "video_detect_type": type_dict[self.detect_type_var.get()]})
            # 断言processes是一个进程对象
            assert isinstance(self.processes, multiprocessing.Process)
            self.processes.start()

        elif source == "本地摄像设备":
            self.process_type = 2
            device_dict = dict((value, key) for key, value in self.video_processor.local_video_device_list)
            self.processes = multiprocessing.Process(
                target=self.local_process_workder, args=(),
                kwargs={
                    "shared_value": self.shared_value,
                    "shared_event": self.shared_event,
                    "video_sourse": int(device_dict[self.video_device_var.get()]),
                    "flag_visibility": self.visibility_var.get(),
                    "flag_save": self.save_var.get(),
                    "flag_detect": self.detect_var.get(),
                    "video_detect_sensitivity": self.sensitivity_var.get(),
                    "video_detect_type": type_dict[self.detect_type_var.get()]})
            # 断言processes是一个进程对象
            assert isinstance(self.processes, multiprocessing.Process)
            self.processes.start()

        elif source == "网络摄像设备":
            self.process_type = 3
            self.processes = multiprocessing.Process(
                target=self.device_process_workder, args=(),
                kwargs={
                    "shared_value": self.shared_value,
                    "shared_event": self.shared_event,
                    "video_sourse": self.date_url,
                    "flag_visibility": self.visibility_var.get(),
                    "flag_save": self.save_var.get(),
                    "flag_detect": self.detect_var.get(),
                    "video_detect_sensitivity": self.sensitivity_var.get(),
                    "video_detect_type": type_dict[self.detect_type_var.get()]})
            # 断言processes是一个进程对象
            assert isinstance(self.processes, multiprocessing.Process)
            self.processes.start()
        self.video_processor.logger.log_write(f"Start the {source} worker process", Log_Processor.INFO)

        self.loading_window = tk.Toplevel(self.root)
        self.loading_window.title("开始执行任务")
        label = tk.Label(self.loading_window, font=self.label_font, text="正在初始化任务中，请稍等")
        label.pack(padx=20, pady=20)
        self.center_window(self.loading_window, 300, 80)
        self.root.update_idletasks()

    def stop_monitoring(self):
        """
        与主窗口的“停止”按钮绑定，用于停止当前执行任务，恢复ui界面的子进程
        与其他模块进行交互，同样是连接前后端的关键函数
        """
        # 如果没有执行任务的进程不做任何处理
        if self.process_type != 0:
            # 传递关闭信息
            self.shared_event.set()
            self.processes.join()
            messagebox.showinfo("提示", "已退出监控")
            # 销毁加载窗口
            if self.loading_window:
                self.loading_window.destroy()
            self.start_button.config(state=tk.NORMAL)  # 将"开始"按钮设为可用
            self.email_button.config(state=tk.NORMAL)  # 将"邮件管理"按钮设为可用
            self.video_processor.load_video_sourse()  # 重新加载视频相关资源
            # 不再处理进程退出的结果
            self.process_type = 0
            self.shared_value.value = -10
            self.shared_event = None
            self.processes = None
            self.video_processor.logger.log_write(f"Finish the worker process", Log_Processor.INFO)

    def on_closing(self):
        """
        与主窗口右上角退出的按钮绑定，用于退出整个进程，关闭全部子进程
        通过进程树的方式杀死子进程
        """
        # 如果子进程存在
        if self.processes is not None:
            parent = psutil.Process(self.processes.pid)
            # 递归终止所有子进程
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
            self.root.destroy()
            self.video_processor.logger.log_write(f"Exit the home security surveillance system. "
                                                  f"Thanks for your using!",
                                                  Log_Processor.INFO)
        # 确保退出程序
        sys.exit(0)

    def email_manage(self):
        """
        与主窗口的“邮件处理”按钮绑定，用于帮助用户管理邮件信息
        """
        # 创建子窗口用于和用户交互处理邮件信息
        email_window = tk.Toplevel(self.root)
        email_window.title("邮件管理")
        self.center_window(email_window, 600, 220)
        self.root.attributes('-disabled', True)
        email_window.protocol('WM_DELETE_WINDOW', lambda: confirm())  # 将关闭按钮与取消函数关联

        def confirm():
            """与邮件处理窗口的提交按钮绑定"""
            self.root.attributes('-disabled', False)  # 将主窗口设为可用
            email_window.destroy()  # 关闭窗口
            return

        def change_sender():
            """用户修改发件人按钮绑定"""
            change_sender_window = tk.Toplevel(email_window)
            self.center_window(change_sender_window, 340, 150)
            change_sender_window.title("更换发件人")
            email_window.attributes('-disabled', True)
            change_sender_window.protocol('WM_DELETE_WINDOW', lambda: cancel_sender_email())  # 将关闭按钮与取消函数关联
            self.email_label = ttk.Label(change_sender_window, text="邮箱:")
            self.email_label.grid(row=0, column=0, padx=5, pady=10)
            self.password_label = ttk.Label(change_sender_window, text="密码:")
            self.password_label.grid(row=1, column=0, padx=5, pady=10)
            input_email = tk.StringVar()
            input_email_entry = ttk.Entry(change_sender_window, font=self.label_font, textvariable=input_email,
                                          width=30)
            input_email_entry.grid(row=0, column=1, padx=5, pady=10)
            input_password = tk.StringVar()
            input_password_entry = ttk.Entry(change_sender_window, font=self.label_font, textvariable=input_password,
                                             width=30)
            input_password_entry.grid(row=1, column=1, padx=5, pady=10)

            def confirm_sender_email():
                """验证修改发件人窗口的按钮绑定"""
                warning_processor = Warning_Processor()
                if warning_processor.append_email_senter(input_email.get(), input_password.get()):
                    self.sender_info_label.destroy()
                    if warning_processor.email_senter_data:
                        self.sender_info_label = ttk.Label(email_window,
                                                           text=warning_processor.email_senter_data['email'])
                    else:
                        self.sender_info_label = ttk.Label(email_window, text="无发件人")
                    self.sender_info_label.grid(row=0, column=1, pady=10, sticky='W')
                    self.video_processor.logger.log_write(f"Finish appending sender",
                                                          Log_Processor.INFO)
                else:
                    messagebox.showwarning("提示", "更改失败，请检查邮箱地址或密码是否正确")
                    self.video_processor.logger.log_write(f"Fail to append sender, please check the input",
                                                          Log_Processor.WARNING)
                email_window.attributes('-disabled', False)  # 将主窗口设为可用
                change_sender_window.destroy()  # 关闭窗口
                return

            def cancel_sender_email():
                """取消修改发件人窗口的按钮绑定"""
                email_window.attributes('-disabled', False)  # 将主窗口设为可用
                change_sender_window.destroy()  # 关闭窗口
                return

            bottom = tk.Frame(change_sender_window)
            bottom.grid(row=2, column=0, columnspan=2)
            c = tk.Frame(bottom)
            c.pack(fill="x")
            confirm_button = ttk.Button(c, text="提交", command=confirm_sender_email)
            confirm_button.grid(row=0, column=0, padx=20, pady=10)
            cancel_button = ttk.Button(c, text="取消", command=cancel_sender_email)
            cancel_button.grid(row=0, column=1, padx=20, pady=10)

        def append_receiver():
            """用户添加收件人的按钮绑定"""
            append_receiver_window = tk.Toplevel(email_window)
            self.center_window(append_receiver_window, 340, 110)
            append_receiver_window.title("添加收件人")
            email_window.attributes('-disabled', True)
            append_receiver_window.protocol('WM_DELETE_WINDOW', lambda: cancel_receiver_email())  # 将关闭按钮与取消函数关联
            self.email_label = ttk.Label(append_receiver_window, text="邮箱:")
            self.email_label.grid(row=0, column=0, padx=5, pady=10)
            input_email = tk.StringVar()
            input_email_entry = ttk.Entry(append_receiver_window, font=self.label_font, textvariable=input_email,
                                          width=30)
            input_email_entry.grid(row=0, column=1, padx=5, pady=10)

            def confirm_receiver_email():
                """验证修改收件人窗口的按钮绑定"""
                warning_processor = Warning_Processor()
                if warning_processor.append_email_receiver(input_email.get()):
                    if input_email.get() not in self.listbox.get(0, tk.END):
                        self.video_processor.logger.log_write(f"Finish appending receiver.",
                                                              Log_Processor.INFO)
                        self.listbox.insert(tk.END, input_email.get())
                    else:
                        self.video_processor.logger.log_write(f"Fail to append receiver, the address is exist",
                                                              Log_Processor.WARNING)
                        messagebox.showwarning("提示", "添加失败，该邮箱地址已存在")
                else:
                    self.video_processor.logger.log_write(f"Fail to append receiver, please check the input",
                                                          Log_Processor.WARNING)
                    messagebox.showwarning("提示", "添加失败，请检查邮箱地址是否正确")
                email_window.attributes('-disabled', False)  # 将主窗口设为可用
                append_receiver_window.destroy()  # 关闭窗口
                return

            def cancel_receiver_email():
                """取消修改收件人窗口的按钮绑定"""
                email_window.attributes('-disabled', False)  # 将主窗口设为可用
                append_receiver_window.destroy()  # 关闭窗口
                return

            bottom = tk.Frame(append_receiver_window)
            bottom.grid(row=2, column=0, columnspan=2)
            c = tk.Frame(bottom)
            c.pack(fill="x")
            confirm_button = ttk.Button(c, text="提交", command=confirm_receiver_email)
            confirm_button.grid(row=0, column=0, padx=20, pady=10)
            cancel_button = ttk.Button(c, text="取消", command=cancel_receiver_email)
            cancel_button.grid(row=0, column=1, padx=20, pady=10)

        def delete_receiver():
            """用户删除收件人的按钮绑定"""
            selected_indices = self.listbox.curselection()
            warning_processor = Warning_Processor()
            for index in selected_indices[::-1]:
                if warning_processor.delete_email_receiver(self.listbox.get(index)):
                    self.listbox.delete(index)
                    self.video_processor.logger.log_write(f"Finish deleting receiver.",
                                                          Log_Processor.INFO)
                else:
                    self.video_processor.logger.log_write(f"Fail to delete receiver, please check the input",
                                                          Log_Processor.WARNING)
                    messagebox.showwarning("提示", "删除失败，请检查邮箱地址是否正确")

        # 完成子窗口界面设置和映射
        warning_processor = Warning_Processor()
        self.sender_label = ttk.Label(email_window, text="发件人信息:")
        self.sender_label.grid(row=0, column=0, padx=5, pady=10)
        if warning_processor.email_senter_data:
            self.sender_info_label = ttk.Label(email_window,
                                               text=warning_processor.email_senter_data['email'])
        else:
            self.sender_info_label = ttk.Label(email_window, text="无发件人")
        self.sender_info_label.grid(row=0, column=1, pady=10, sticky='W')
        self.change_sender_button = ttk.Button(email_window, text="更换", command=change_sender)
        self.change_sender_button.grid(row=0, column=2, padx=10, pady=10)

        self.receiver_label = ttk.Label(email_window, text="收件人列表:")
        self.receiver_label.grid(row=1, column=0, padx=5, pady=10)

        frame = ttk.Frame(email_window)
        frame.grid(row=1, column=1, sticky='W')

        # Listbox
        self.listbox = tk.Listbox(frame, font=self.label_font, height=5, width=25, selectmode=tk.EXTENDED)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # 垂直滚动条
        self.v_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # 将滚动条连接到Listbox
        self.listbox.config(yscrollcommand=self.v_scrollbar.set)
        # 添加列表项
        for item in warning_processor.email_receiver_data:
            self.listbox.insert(tk.END, item)

        self.append_receiver_button = ttk.Button(email_window, text="添加", command=append_receiver)
        self.delete_receiver_button = ttk.Button(email_window, text="删除", command=delete_receiver)
        self.append_receiver_button.grid(row=1, column=2, padx=10, pady=10)
        self.delete_receiver_button.grid(row=1, column=3, padx=10, pady=10)

        bottom = tk.Frame(email_window)
        bottom.grid(row=2, column=0, columnspan=4)
        c = tk.Frame(bottom)
        c.pack(fill="x")
        confirm_button = ttk.Button(c, text="确认信息", command=confirm)
        confirm_button.grid(row=0, column=0, padx=30, pady=10)

    # # 与“测试”按钮绑定
    # def start_test(self):
    #     type_dict = {'全部': 0, '火焰': 1, '人员': 2, '异常情况': 3}
    #     print(self.visibility_var.get())
    #     print(self.detect_var.get())
    #     print(type_dict[self.detect_type_var.get()])
    #     print(self.save_var.get())
    #     print(self.sensitivity_var.get())

    @staticmethod
    def history_video_process_workder(shared_value, shared_event, video_strat_save_date, video_index,
                                      flag_visibility, flag_re_detect, video_detect_sensitivity, video_detect_type):
        """
        处理本地历史视频进程的工作函数，除共享内存对象和进程事件通信对象外
        其他传入参数类型和意义与视频流处理器的对应处理函数相同
        是一个静态方法，只通过传递的共享内存对象和进程事件通信对象进行进程间的交互
        """
        vp = Video_Processor(url_capture_time_out=10,
                             event=shared_event, return_value=shared_value)
        vp.load_history_video(video_strat_save_date=video_strat_save_date,
                              video_index=video_index,
                              flag_visibility=flag_visibility,
                              flag_re_detect=flag_re_detect,
                              video_detect_sensitivity=video_detect_sensitivity,
                              video_detect_type=video_detect_type)

    @staticmethod
    def local_process_workder(shared_value, shared_event, video_sourse, flag_visibility,
                              flag_save, flag_detect, video_detect_sensitivity, video_detect_type):
        """
        处理本地视频设备进程的工作函数，除共享内存对象和进程事件通信对象外
        其他传入参数类型和意义与视频流处理器的对应处理函数相同
        是一个静态方法，只通过传递的共享内存对象和进程事件通信对象进行进程间的交互
        """
        vp = Video_Processor(url_capture_time_out=10,
                             event=shared_event, return_value=shared_value)
        vp.load_local_video_device(video_sourse=video_sourse,
                                   flag_visibility=flag_visibility,
                                   flag_save=flag_save,
                                   flag_detect=flag_detect,
                                   video_detect_sensitivity=video_detect_sensitivity,
                                   video_detect_type=video_detect_type)

    @staticmethod
    def device_process_workder(shared_value, shared_event, video_sourse, flag_visibility,
                               flag_save, flag_detect, video_detect_sensitivity, video_detect_type):
        """
        处理网络视频设备进程的工作函数，除共享内存对象和进程事件通信对象外
        其他传入参数类型和意义与视频流处理器的对应处理函数相同
        是一个静态方法，只通过传递的共享内存对象和进程事件通信对象进行进程间的交互
        """
        vp = Video_Processor(url_capture_time_out=10,
                             event=shared_event, return_value=shared_value)
        vp.load_network_video_device(video_sourse=video_sourse,
                                     flag_visibility=flag_visibility,
                                     flag_save=flag_save,
                                     flag_detect=flag_detect,
                                     video_detect_sensitivity=video_detect_sensitivity,
                                     video_detect_type=video_detect_type)

    def check_video_processor(self):
        """
        定义检查函数，每隔1s调用一次自身，
        用于检查正在处理视频流的Video_Processor进程实例是否结束，并刷新当前可用的本地视频设备
        如果未结束相当于只刷新本地视频设备，如果已结束会弹出进程返回错误信息所相应的提示窗口
        """
        # process_type为1则为本地历史视频进程
        if self.process_type == 1:
            # 返回错误类型的对应信息
            if self.shared_value.value == 1:
                messagebox.showwarning("提示", "历史保存视频文件夹为空\n请检查文件是否存在")
            elif self.shared_value.value == 2:
                messagebox.showwarning("提示", "要加载视频的日期无视频文件\n请检查文件是否存在")
            elif self.shared_value.value == 3:
                messagebox.showwarning("提示", "找不到该视频文件，索引不存在\n请检查文件是否存在")
            elif self.shared_value.value == -1:
                messagebox.showwarning("提示", "视频流打开失败\n请检查文件格式是否正确")
            elif self.shared_value.value == -2:
                messagebox.showwarning("提示", "视频流意外关闭\n请检查文件是否完好")
            elif self.shared_value.value == 0:
                messagebox.showinfo("提示", "监控进程已完成退出")
            elif self.shared_value.value == -9:
                # 销毁加载窗口
                if self.loading_window:
                    self.loading_window.destroy()
            # 处理进程退出的后的ui变化
            if self.shared_value.value != -10 and self.shared_value.value != -9:
                # 销毁加载窗口
                if self.loading_window:
                    self.loading_window.destroy()
                self.process_type = 0
                self.shared_value.value = -10
                self.shared_event = None
                self.processes = None
                self.start_button.config(state=tk.NORMAL)  # 将"开始"按钮设为可用
                self.email_button.config(state=tk.NORMAL)  # 将"邮件管理"按钮设为可用
                self.video_processor.load_video_sourse()  # 重新加载视频相关资源
                self.video_processor.logger.log_write(f"Finish the worker process", Log_Processor.INFO)

        # process_type为2则为本地视频设备进程
        elif self.process_type == 2:
            # 返回错误类型的对应信息
            if self.shared_value.value == 1:
                messagebox.showwarning("提示", "本地视频设备为空\n请检查本地是否有视频设备")
            elif self.shared_value.value == 2:
                messagebox.showwarning("提示", "索引号超过了本地视频设备列表大小\n请检查本地视频设备列表")
            elif self.shared_value.value == -1:
                messagebox.showwarning("提示", "摄像头打开失败\n请检查或重新选择摄像头")
            elif self.shared_value.value == -2:
                messagebox.showwarning("提示", "摄像头下一帧读取失败\nn请检查摄像头是否被关闭")
            elif self.shared_value.value == -3:
                messagebox.showwarning("提示", "保存视频文件时，创建目录或打开视频文件失败")
            elif self.shared_value.value == 0:
                messagebox.showinfo("提示", "监控进程已完成退出")
            elif self.shared_value.value == -9:
                # 销毁加载窗口
                if self.loading_window:
                    self.loading_window.destroy()
            # 处理进程退出的后的ui变化
            if self.shared_value.value != -10 and self.shared_value.value != -9:
                # 销毁加载窗口
                if self.loading_window:
                    self.loading_window.destroy()
                self.process_type = 0
                self.shared_value.value = -10
                self.shared_event = None
                self.processes = None
                self.start_button.config(state=tk.NORMAL)  # 将"开始"按钮设为可用
                self.email_button.config(state=tk.NORMAL)  # 将"邮件管理"按钮设为可用
                self.video_processor.load_video_sourse()  # 重新加载视频相关资源
                self.video_processor.logger.log_write(f"Finish the worker process", Log_Processor.INFO)

        # process_type为3则为网络视频设备进程
        elif self.process_type == 3:
            # 返回错误类型的对应信息
            if self.shared_value.value == 1:
                messagebox.showwarning("提示", "网络视频设备为空\n请检查是否有已保存的url地址")
            elif self.shared_value.value == 2:
                messagebox.showwarning("提示", "网络设备视频传输协议不支持\n请使用rtsp、http等格式的传输协议")
            elif self.shared_value.value == 3:
                messagebox.showwarning("提示", "从url获取视频流失败\n请检查连接是否正常")
            elif self.shared_value.value == -1:
                messagebox.showwarning("提示", "摄像头打开超时\n请检查url地址和对应的网络摄像头状态")
            elif self.shared_value.value == -2:
                messagebox.showwarning("提示", "摄像头下一帧读取失败\n请检查摄像头是否被关闭")
            elif self.shared_value.value == -3:
                messagebox.showwarning("提示", "保存视频文件时，创建目录或打开视频文件失败")
            elif self.shared_value.value == 0:
                messagebox.showinfo("提示", "监控进程已完成退出")
            elif self.shared_value.value == -9:
                # 销毁加载窗口
                if self.loading_window:
                    self.loading_window.destroy()
            # 处理进程退出的后的ui变化
            if self.shared_value.value != -10 and self.shared_value.value != -9:
                # 销毁加载窗口
                if self.loading_window:
                    self.loading_window.destroy()
                self.process_type = 0
                self.shared_value.value = -10
                self.shared_event = None
                self.processes = None
                self.start_button.config(state=tk.NORMAL)  # 将"开始"按钮设为可用
                self.email_button.config(state=tk.NORMAL)  # 将"邮件管理"按钮设为可用
                self.video_processor.load_video_sourse()   # 重新加载视频相关资源
                self.video_processor.logger.log_write(f"Finish the worker process", Log_Processor.INFO)

        # 如果没有执行的进程，刷新本地摄像设备
        else:
            # 如果本地设备更新了且目前是本地摄像设备，更新相关的内容
            if self.video_processor.update_local_video_sourse():
                if self.source_var.get() == "本地摄像设备":
                    self.video_device_var = tk.StringVar()
                    if self.video_processor.local_video_device_list:
                        # 之前选择设备无法捕捉时，刷新为第一个可选的
                        if not self.video_device_var.get() in self.video_processor.local_video_device_list:
                            self.video_device_var.set(self.video_processor.local_video_device_list[0][1])
                    else:
                        self.video_device_var.set('')
                    self.video_device_options = [''] + list(value for _, value in
                                                            self.video_processor.local_video_device_list)
                    self.video_device_menu = ttk.OptionMenu(self.root, self.video_device_var,
                                                            *self.video_device_options)
                    self.video_device_menu.grid(row=1, column=1, pady=10, columnspan=2, sticky='W')
                    self.video_device_menu['menu'].config(font=self.label_font)

        # 重复检查
        self.root.after(ms=1000, func=self.check_video_processor)
        return

## 模块单元测试部分 ##
if __name__ == "__main__":

    # Ui界面测试需要用按键触发
    app = VideoMonitorApp(tk.Tk())
    # 测试定时器是否正常工作
    app.root.after(ms=1000, func=app.check_video_processor)
    app.root.mainloop()

