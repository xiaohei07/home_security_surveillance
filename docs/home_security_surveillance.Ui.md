# home_security_surveillance.Ui package

## Submodules

## home_security_surveillance.Ui.ui module

File Name: ui.py
Author: Captain
Date: 2024-06-06
Version: 1.5
Description: 提供简洁的图形化界面

### *class* home_security_surveillance.Ui.ui.VideoMonitorApp(root)

基类：`object`

根据用户的操作完成相应的家庭监控设置和分析，是家庭监控系统的用户交互和任务分发部分

* **参数:**
  **root** (*tk.TK*) – 用于创建和用户进行交互的主窗口

#### root

和用户进行交互的主窗口，在上面可以定义各种控件

* **Type:**
  tk.TK

#### video_processor

视频流处理器的一个实例，此处是一个静态实例，不执行任务，主要用于获得各种视频设备和视频文件信息

* **Type:**
  [Video_Processor](home_security_surveillance.Video_process.md#home_security_surveillance.Video_process.video_processor.Video_Processor)

#### process_type

执行任务的进程对应的进程类型，0表示没有执行任务的进程，1表示执行加载和处理本地历史视频任务的进程，
2表示执行加载和处理本地视频设备任务的进程，3表示执行加载和处理网络视频设备任务的进程

* **Type:**
  int

#### processes

存储multiprocessing进程对象的成员变量，是执行任务进程的句柄

* **Type:**
  multiprocessing.Process

#### shared_value

为其他进程所共享的共享内存对象，创建为一个整型，默认为-10，用于保存其他进程的返回值
根据不为-10的返回值可以确定错误情况

* **Type:**
  multiprocessing.Value

#### shared_event

进程事件通信对象，用于通知执行任务进程是否停止，每次创建执行任务进程时刷新

* **Type:**
  multiprocessing.Event

### 备注

在该类中加载了静态视频处理对象，每次创建进程执行任务时需要加载一个动态的视频处理对象，此时不会产生IO冲突
类内创建了各种控件，此处不再一一说明

### 示例

#### *static* center_window(window: Toplevel | Tk, width: int, height: int)

窗口居中设置函数，静态方法
:param window: 要设置居中的窗口对象，可以是主窗口或者其他顶层窗口
:type window: Union[tk.Toplevel, tk.TK]
:param width: 窗口的宽度
:type width: int
:param height: 窗口的高度
:type height: int

#### check_start()

根据三个Checkbutton对应的Var的状态，检查开始按钮是否可以点击

#### check_video_processor()

定义检查函数，每隔1s调用一次自身，
用于检查正在处理视频流的Video_Processor进程实例是否结束，并刷新当前可用的本地视频设备
如果未结束相当于只刷新本地视频设备，如果已结束会弹出进程返回错误信息所相应的提示窗口

#### confirm_source(value: str)

确定资源信息函数，用于选择视频设备类型时的处理，与主窗口选择视频类型的操作列表绑定
此处在有需要时会在主窗口上创建子窗口完成相应处理
:param value: 读取到的用户选择的视频设备类型字符串名陈
:type value: str

#### create_widgets()

添加窗口组件函数，用于创建大部分主窗口上的组件

#### *static* device_process_workder(shared_value, shared_event, video_sourse, flag_visibility, flag_save, flag_detect, video_detect_sensitivity, video_detect_type)

处理网络视频设备进程的工作函数，除共享内存对象和进程事件通信对象外
其他传入参数类型和意义与视频流处理器的对应处理函数相同
是一个静态方法，只通过传递的共享内存对象和进程事件通信对象进行进程间的交互

#### email_manage()

与主窗口的“邮件处理”按钮绑定，用于帮助用户管理邮件信息

#### *static* history_video_process_workder(shared_value, shared_event, video_strat_save_date, video_index, flag_visibility, flag_re_detect, video_detect_sensitivity, video_detect_type)

处理本地历史视频进程的工作函数，除共享内存对象和进程事件通信对象外
其他传入参数类型和意义与视频流处理器的对应处理函数相同
是一个静态方法，只通过传递的共享内存对象和进程事件通信对象进行进程间的交互

#### *static* local_process_workder(shared_value, shared_event, video_sourse, flag_visibility, flag_save, flag_detect, video_detect_sensitivity, video_detect_type)

处理本地视频设备进程的工作函数，除共享内存对象和进程事件通信对象外
其他传入参数类型和意义与视频流处理器的对应处理函数相同
是一个静态方法，只通过传递的共享内存对象和进程事件通信对象进行进程间的交互

#### on_closing()

与主窗口右上角退出的按钮绑定，用于退出整个进程，关闭全部子进程
通过进程树的方式杀死子进程

#### start_monitoring()

与主窗口的“开始”按钮绑定，用于创建执行任务的子进程
与其他模块进行交互，是连接前后端的关键函数

#### stop_monitoring()

与主窗口的“停止”按钮绑定，用于停止当前执行任务，恢复ui界面的子进程
与其他模块进行交互，同样是连接前后端的关键函数

## Module contents
