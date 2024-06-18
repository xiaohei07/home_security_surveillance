# -*- coding: utf-8 -*-
"""
File Name: ui.py
Author: Captain
Date: 2024-06-16
Version: 1.0
Description: 提供简洁的图形化界面
"""
# 引入常用库
from home_security_surveillance.Common import *
from tkinter import filedialog
from tkinter import messagebox
# 引入PyCameraList.camera_device库的list_video_devices函数，用于列出所有可用的视频源
from PyCameraList.camera_device import list_video_devices
# 引入video_processor库
from home_security_surveillance.Video_process import *


class VideoMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("家庭视频监控软件")
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)
        self.create_widgets()

    # 添加窗口组件
    def create_widgets(self):
        # 选择视频来源
        self.source_label = ttk.Label(self.root, text="选择视频来源:")
        self.source_label.grid(row=0, column=0, padx=20, pady=10)
        self.source_var = tk.StringVar()
        self.source_var.set("本地摄像设备")
        self.source_options = ["", "本地历史视频", "本地摄像设备", "网络摄像设备"]
        self.source_menu = ttk.OptionMenu(self.root, self.source_var, *self.source_options, command=self.confirm_source)
        self.source_menu.grid(row=0, column=1, pady=10, columnspan=2, sticky='W')
        self.date_url = ''

        # 选择可用设备或视频
        self.video_device_label = ttk.Label(self.root, text="选择可用设备:")
        self.video_device_label.grid(row=1, column=0, padx=20, pady=10)
        self.video_device_var = tk.StringVar()
        self.video_device_var.set(list_video_devices()[0][1])
        self.video_device_options = ['']+list(value for _, value in list_video_devices())
        self.video_device_menu = ttk.OptionMenu(self.root, self.video_device_var, *self.video_device_options)
        self.video_device_menu.grid(row=1, column=1, pady=10, columnspan=2, sticky='W')

        # self.open_button = ttk.Button(self.root, text="选择文件", command=self.select_file)
        # self.open_button.pack(pady=5)

        # 选择处理方式
        self.process_mode_label = ttk.Label(self.root, text="选择处理方式:")
        self.process_mode_label.grid(row=2, column=0, padx=20, pady=10)
        self.bottom1 = tk.Frame(self.root)
        self.bottom1.grid(row=2, column=1, columnspan=2)
        c1 = tk.Frame(self.bottom1)
        c1.pack(fill="x")
        self.visibility_var = tk.BooleanVar()
        self.visibility_check = ttk.Checkbutton(c1, text="可视化", variable=self.visibility_var)
        self.visibility_var.set(True)
        self.visibility_check.grid(row=0, column=0, padx=10, pady=10)

        self.detect_var = tk.BooleanVar()
        self.detect_check = ttk.Checkbutton(c1, text="检测", variable=self.detect_var)
        self.detect_check.grid(row=0, column=1, padx=10, pady=10)

        self.save_var = tk.BooleanVar()
        self.save_check = ttk.Checkbutton(c1, text="录制", variable=self.save_var)
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
        self.bottom2.grid(row=4, column=1)
        c2 = tk.Frame(self.bottom2)
        c2.pack(fill="x")
        self.sensitivity_var = tk.IntVar()
        self.sensitivity_var.set(1)
        self.sensitivity_low = ttk.Radiobutton(c2, text="低", variable=self.sensitivity_var, value=0)
        self.sensitivity_low.grid(row=0, column=0, padx=0, pady=10)
        self.sensitivity_high = ttk.Radiobutton(c2, text="高", variable=self.sensitivity_var, value=1)
        self.sensitivity_high.grid(row=0, column=1, padx=30, pady=10)

        # 开始和停止按钮
        self.bottom3 = tk.Frame(self.root)
        self.bottom3.grid(row=5, column=0, columnspan=3)
        c3 = tk.Frame(self.bottom3)
        c3.pack(fill="x")
        c3.columnconfigure(0, weight=1)
        c3.columnconfigure(1, weight=1)
        self.start_button = ttk.Button(c3, text="开始", command=self.start_monitoring)
        self.stop_button = ttk.Button(c3, text="停止", command=self.stop_monitoring)
        self.start_button.grid(row=0, column=0, padx=20, pady=10)
        self.stop_button.grid(row=0, column=1, padx=20, pady=10)

        # 测试按钮
        # self.start_button = ttk.Button(self.root, text="测试", command=self.start_test)
        # self.start_button.grid(row=6, column=0, pady=10)

    # 用于确认视频来源
    def confirm_source(self, value):
        def choose_address(sub_value):
            input.set(sub_value)

        if value == "本地摄像设备":
            self.video_device_var.set(list_video_devices()[0][1])
            self.video_device_options = ['']+list(value for _, value in list_video_devices())
            self.video_device_menu.destroy()
            self.video_device_menu = ttk.OptionMenu(self.root, self.video_device_var, *self.video_device_options)
            self.video_device_menu.grid(row=1, column=1, pady=10, columnspan=2, sticky='W')
            self.video_device_label.destroy()
            self.video_device_label = ttk.Label(self.root, text="选择可用设备:")
            self.video_device_label.grid(row=1, column=0, pady=10)
            return

        input_window = tk.Toplevel(root)
        root.attributes('-disabled', True)
        input_window.protocol('WM_DELETE_WINDOW', lambda: cancel())  # 将关闭按钮与取消函数关联
        input = tk.StringVar()
        input_entry = tk.Entry(input_window, textvariable=input, width=30)

        if value == "本地历史视频":
            input_window.title("输入视频日期")
            tk.Label(input_window, text="输入视频日期:").grid(row=0, column=0, padx=5, pady=20)
            input.set('（示例:2024-10-01）')
            self.video_device_label.destroy()
            self.video_device_label = ttk.Label(self.root, text="选择可用视频:")
            self.video_device_label.grid(row=1, column=0, pady=10)

        elif value == "网络摄像设备":
            input_window.title("输入摄像头地址")
            tk.Label(input_window, text="输入设备地址:").grid(row=0, column=0, padx=5, pady=20)
            address_label = ttk.Label(input_window, text="选择已有地址:")
            address_label.grid(row=1, column=0, padx=5, pady=10)
            video_process = Video_Processor(url_capture_time_out=10, root=self.root)
            url_list = [list(d.values())[0] for d in video_process.nvd_processor.nvd_config_data]
            address_var = tk.StringVar()
            address_var.set(url_list[0])
            address_options = ['']+url_list
            address_menu = ttk.OptionMenu(input_window, address_var, *address_options, command=choose_address)
            address_menu.grid(row=1, column=1, pady=10, sticky='W')
            self.video_device_label.destroy()
            self.video_device_label = ttk.Label(self.root, text="选择可用设备:")
            self.video_device_label.grid(row=1, column=0, pady=10)

        input_entry.grid(row=0, column=1, padx=5, pady=10)

        # 与“提交”按钮绑定
        def submit():
            self.date_url = input_entry.get()

            if value == "本地历史视频":
                video_process = Video_Processor(url_capture_time_out=10, root=self.root)
                try:
                    video_list = [d[1] for d in video_process.hs_processor.hv_dict[self.date_url].values()]
                except KeyError:
                    messagebox.showwarning("提示", "日期格式错误或该日期下无视频\n请重新输入日期")
                self.video_device_var.set(video_list[0])
                self.video_device_options = ['']+video_list
                self.video_device_menu.destroy()
                self.video_device_menu = ttk.OptionMenu(self.root, self.video_device_var, *self.video_device_options)
                self.video_device_menu.grid(row=1, column=1, pady=10, columnspan=2, sticky='W')

            elif value == "网络摄像设备":
                self.video_device_var.set(self.date_url)
                self.video_device_options = ['',self.date_url]
                self.video_device_menu.destroy()
                self.video_device_menu = ttk.OptionMenu(self.root, self.video_device_var, *self.video_device_options)
                self.video_device_menu.grid(row=1, column=1, pady=10, columnspan=2, sticky='W')

            self.video_device_menu = ttk.OptionMenu(self.root, self.video_device_var, *self.video_device_options)
            root.attributes('-disabled', False)  # 将主窗口设为可用
            input_window.destroy()  # 关闭窗口
            return


        # 与“取消”按钮绑定
        def cancel():
            root.attributes('-disabled', False)  # 将主窗口设为可用
            self.video_device_var.set('')  # 取消已选项目
            self.video_device_options.clear()  # 删除可选项目
            input_window.destroy()  # 关闭窗口
            return

        self.bottom = tk.Frame(input_window)
        self.bottom.grid(row=2, column=0, columnspan=2)
        c = tk.Frame(self.bottom)
        c.pack(fill="x")
        c.columnconfigure(0, weight=1)
        c.columnconfigure(1, weight=1)
        submit_button = tk.Button(c, text="提交", command=submit)
        cancel_button = tk.Button(c, text="取消", command=cancel)
        submit_button.grid(row=0, column=0, padx=30, pady=10)
        cancel_button.grid(row=0, column=1, padx=30, pady=10)

    # 用于上传文件
    # def select_file(self):
    #     self.file_path = filedialog.askopenfilename()

    # 与“开始”按钮绑定
    def start_monitoring(self):
        video_process = Video_Processor(url_capture_time_out=10, root=self.root)
        type_dict = {'全部': 0, '火焰': 1, '人员': 2, '异常情况': 3}
        source = self.source_var.get()
        if source == "本地历史视频":
            video_index_dict = {val[1]: key for key, val in video_process.hs_processor.hv_dict[self.date_url].items()}
            ret = video_process.load_history_video(video_strat_save_date=self.date_url,
                                                   video_index=video_index_dict[self.video_device_var.get()],
                                                   flag_visibility=self.visibility_var.get(),
                                                   flag_re_detect=self.detect_var.get(),
                                                   video_deetect_type=type_dict[self.detect_type_var.get()])
            if ret == 1 or ret == 2 or ret == 3:
                messagebox.showwarning("提示", "找不到该视频文件\n请检查文件是否存在")
            elif ret == -1:
                messagebox.showwarning("提示", "视频流打开失败\n请检查文件格式是否正确")
            elif ret == -2:
                messagebox.showwarning("提示", "视频流意外关闭\n请检查文件是否完好")
        elif source == "本地摄像设备":
            device_dict = dict((value, key) for key, value in list_video_devices())
            ret = video_process.load_local_video_device(video_sourse=int(device_dict[self.video_device_var.get()]),
                                                        flag_visibility=self.visibility_var.get(),
                                                        flag_save=self.save_var.get(),
                                                        flag_detect=self.detect_var.get(),
                                                        video_deetect_type=type_dict[self.detect_type_var.get()])
            if ret == 1 or ret == 2 or ret == -1:
                messagebox.showwarning("提示", "打开摄像头失败\n请检查或重新选择摄像头")
            elif ret == -2:
                messagebox.showwarning("提示", "读取摄像头下一帧失败\n请检查摄像头是否被关闭")
            elif ret == -3:
                messagebox.showwarning("提示", "保存视频文件时，创建目录或打开视频文件失败")

        elif source == "网络摄像设备":
            ret = video_process.load_network_video_device(video_sourse=self.date_url,
                                                          flag_visibility=self.visibility_var.get(),
                                                          flag_save=self.save_var.get(),
                                                          flag_detect=self.detect_var.get(),
                                                          video_deetect_type=type_dict[self.detect_type_var.get()])
            if ret == 1 or ret == 2 or ret == -1:
                messagebox.showwarning("提示", "打开摄像头失败\n请输入正确的地址")
            elif ret == 3:
                messagebox.showwarning("提示", "从url获取视频流失败\n请检查连接是否正常")
            elif ret == -2:
                messagebox.showwarning("提示", "读取摄像头下一帧失败\n请检查摄像头是否被关闭")
            elif ret == -3:
                messagebox.showwarning("提示", "保存视频文件时，创建目录或打开视频文件失败")

    # 与“停止”按钮绑定
    def stop_monitoring(self):
        pass

    # 与“测试”按钮绑定
    def start_test(self):
        type_dict = {'全部': 0, '火焰': 1, '人员': 2, '异常情况': 3}
        print(self.visibility_var.get())
        print(self.detect_var.get())
        print(type_dict[self.detect_type_var.get()])
        print(self.save_var.get())
        print(self.sensitivity_var.get())


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoMonitorApp(root)
    root.mainloop()
