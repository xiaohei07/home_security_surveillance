# home_security_surveillance.Video_process package

## Submodules

## home_security_surveillance.Video_process.video_capture_process module

File Name: video_capture_process.py
Author: 07xiaohei
Date: 2024-05-15
Version: 1.1
Description: 用于opencv在捕捉url信息减少超时时间的进程类

### *class* home_security_surveillance.Video_process.video_capture_process.Video_Capture_Process(url, timeout, result_queue)

基类：`Process`

多进程类，利用opencv的VideoCapture函数测试url是否可以获得视频流

* **参数:**
  * **url** (*str*) – 用于捕捉视频流的url地址
  * **result_queue** (*multiprocessing.Queue*) – 用于接收创建的VideoCapture对象是否成功标志的队列

#### url

用于捕捉视频流的url地址

* **Type:**
  str

#### result_queue

用于接收创建的VideoCapture对象是否成功标志的队列

* **Type:**
  multiprocessing.Queue

#### run()

进程处理的部分,向队列输入一个布尔值

## home_security_surveillance.Video_process.video_detect module

File Name: video_detect.py
Author: youyou
Date: 2024-05-02
Version: 1.5
Description: 使用yolov8，对视频帧进行识别，判断监控是否出现了火灾/人/异常行为

### *class* home_security_surveillance.Video_process.video_detect.Video_Detector(root_dir, use_defalut_parameter)

基类：`object`

视频检测处理器，用于读取部分实时帧完成对应任务的识别功能，是自动检测和识别的核心模块
使用的底层架构为yolov8，火焰模型为自行利用数据集训练，人像识别和异常行为识别直接使用开源模型

* **参数:**
  * **root_dir** (*str*) – 视频检测处理器的根目录，默认值和_config_defaluts中的model-directory对应绝对路径相同
  * **use_defalut_parameter** (*bool*) – 是否使用默认的内置训练参数，否则需要加载配置文件的对应参数，True为使用内置参数，False为不使用

#### root_dir

视频检测处理器的根目录，默认值和_config_defaluts中的model-directory对应绝对路径相同

* **Type:**
  str

### info_logger & error_logger

日志处理器对象的实例，分别用于记录该类活动过程中的运行和错误、报警信息，统一输入到根目录下的info.log和error.log中

* **Type:**
  [Log_Processor](home_security_surveillance.File_process.md#home_security_surveillance.File_process.log.Log_Processor)

### \_train_config & \_predict_config

train_config和predict_config配置文件中的各变量记录，在后续加载时使用，是内部成员，不对外开放接口

* **Type:**
  dict

#### device

标识用户可用于的识别的设备，如果有独显GPU使用独显GPU，否则使用CPU

* **Type:**
  int

#### train_model

被用于训练的预加载模型，仅在训练新模型时使用

* **Type:**
  YOLO

#### predict_model

模式-模型的数字-模型对象字典映射，通过映射可以将模式转变为yolov8要使用的模型对象，直接进行预测
此成员用于加速处理，保证多次调用预测函数或者修改模型内容时，均需要在初始化时加载一次模型即可

* **Type:**
  dict[int, YOLO]

#### model_mode_dict

模式-模型的数字-绝对路径字典映射，通过映射可以将模式转变为yolov8要使用的模型绝对路径
其将相对路径和根路径改为绝对路径，路径根目录用root_dir
1为火焰模型，2为人物模型 3：火焰和人物模型

* **Type:**
  dict[int, str]

#### warning_mode_list

类变量，预测类型和错误码的匹配关系，在检测时需要进行进程的通信，遇到错误需要向视频流处理器通知错误的出现
因此需要将各类型的错误统一映射为一个错误码，视频流处理器通过解码即可获知错误类型

* **Type:**
  list[int]

#### mode_precdict_class

类变量，将使用的mode和预测类别映射为对应的类型，即将映射的错误码1248分别修改为0123

* **Type:**
  dict[int, dict[int, int]]

#### mode_precdict_warning_mode

类变量，将使用的模型mode和预测类别映射为错误码
mode=1对应第一个火焰/烟雾模型，1的预测类别是烟雾，对应错误码是1
0的预测类别是火焰，对应错误码是2，mode=2对应第二个人像识别模型，0的预测类别是人，对应错误码是4
mode=3对应第三个异常行为识别，0的预测类别是跌倒，对应错误码是8

* **Type:**
  dict[int, dict[int, int]]

#### predict_class_type_color_dict

类变量，每个错误类型在绘制错误碰撞箱时使用的颜色，只在使用全部模型模式下有效
第一个键值model对应的mode，第二个键值是预测所得的类型，值为它们的对应颜色

* **Type:**
  dict[int, dict[int, int]]

### ## 训练参数属性集合 ##

#### batch

* **Type:**
  int          每次训练时输入的图片数量，默认为16

#### epochs

* **Type:**
  int         训练迭代的次数，默认为5

#### project

* **Type:**
  str        训练文件存放的目录，默认在根目录下的train_file文件夹下

#### name

* **Type:**
  str           训练过程存放的文件，在project对应目录下创建子目录，存储训练的日志和输出结果

#### imgsz

* **Type:**
  int          输入图片的尺寸，默认要求640\*640

#### data

其默认路径为：ultralytics/cfg/datasets
在该配置文件内按yolov8格式设置好训练集、验证集、测试集的图片路径，类别名等参数

* **Type:**
  str           有关数据集配置文件的路径，由于本项目目标主要是对火焰的识别，在yolov8下默认存放的是fire.yaml

#### weight_pt

* **Type:**
  str      预训练模型的文件名，可用于用户自行完成训练任务，当其不存在时yolov8会自动下载

### ## 预测参数属性集合 ##

#### model_mode

* **Type:**
  int     当用户未指定使用模型时，进行预测默认使用的模式，默认为1，即火焰识别

#### iou

* **Type:**
  float          衡量预测边界框与真实边界框之间重叠程度，用于移除重叠较大的多余边界框，保留最优的检测结果，默认为0.6

#### conf

* **Type:**
  float         模型对识别设置的置信度阈值，低于该阈值的识别结果会被过滤，默认为0.5

#### show

* **Type:**
  bool          模型的预测结果是否可视化，在单独调用模型内部预测函数时可以用来展示结果，默认为True

#### save_dir

* **Type:**
  str       模型预测结果的保存目录，可在其中查看预测获得的识别信息视频和图片

#### max_frame

考虑到大多数摄像头是30帧左右，默认存储1800帧，即保存一分钟左右的视频，可用于保存视频，获知异常出现的前因后果

* **Type:**
  int      从视频流处理器处获得视频帧时，存储的双端队列最大缓冲视频帧数量

### 备注

获取相关参数(可以让用户选择模式)，前端通过修改predict_config.json中的model_mode来改变模式
配置文件的参数都可以和用户进行交互

#### delete_dir(directory: str)

删除目录函数，需要写入日志处理器，不再是静态方法
被删除的目录下不允许有子目录
:param directory: 指定的要删除的目录的绝对路径
:type directory: str

#### detect(frame_queue: Queue, result_queue: Queue, mode: int | None = None, save_dir: str | None = None, max_frame: int | None = None, iou: float | None = None, sensitivity: int = 0)

对摄像头捕捉视频帧的实时检测和处理函数，是视频检测器的核心处理函数
通过多进程的视频帧队列从视频流处理器对象处获得视频帧
并通过另一个队列将检测后的错误码和每个预测类型的对应置信度返回给视频流处理器对象，完成进程通信
:param frame_queue: 视频流对象传入的视频帧队列，用于获得要处理的视频帧队列
:type frame_queue: multiprocessing.Queue
:param result_queue: 返回给视频流对象的处理队列，用于返回错误码和置信度
:type result_queue: multiprocessing.Queue
:param mode: 指定的模式，用户指定后由视频流处理器传给当前的检测器实例，以完成用户要求的检测功能
:type mode: int
:param save_dir: 指定的视频保存路径，目前不提供设置方式，需要在进一步优化后完成设置
:type save_dir: str
:param max_frame: 指定的最大缓冲区帧数，因为无法直接解析视频设备的帧率，故暂未用于实践
:type max_frame: int
:param iou: 指定衡量预测边界框与真实边界框之间重叠程度，未指定(为None)时使用默认值
:type iou: float
:param sensitivity: 指定对异常的敏感程度，0对应低敏感程度，设置置信度阈值为0.6，1对应高敏感程度，设置置信度阈值为0.5，默认为低敏感
:type sensitivity: int

### 备注

传入的视频帧使用具有限定大小的双端队列进行处理
每次从传入视频帧队列中获得全部视频帧按先入先出的顺序进行存储，随后从队列末尾取最实时的视频帧进行检测
这相对于对双端队列中未取出检测的视频帧进行了识别丢帧处理，但能够被保存
最终处理的视频帧比例由设备性能和进程被分配的资源决定
既能保存异常出现的前因后果，又可以保证处理的实时性

#### get_device()

确定进行识别的设备，需要判断GPU是否可用，不可用则使用CPU
如果gpu可用则返回GPU的设备名并日志记录GPU信息，否则日志中记录CPU信息返回CPU字符串
:returns: **device** – GPU的设备编号或者CPU字符串
:rtype: Union[int, torch.device]

#### *static* load_config(path: str)

读取配置文件
:param path: 传入json文件的相对路径
:type path: str

* **返回:**
  **config_data** – 有关参数的字典
* **返回类型:**
  dict

#### make_dir(dir_path: str)

创建空目录函数，需要写入日志处理器，不是静态方法
此处不会检测上一级是否有目录，而是按照目录直接逐级创建
:param dir_path: 指定的要创建的目录的绝对路径
:type dir_path: str

#### mode_precdict_class *= {1: {0: 1, 1: 0}, 2: {0: 2}, 3: {0: 3}}*

noindex:

#### mode_precdict_warning_mode *= {1: {0: 2, 1: 1}, 2: {0: 4}, 3: {0: 8}}*

noindex:

#### model_mode_dict

noindex:

#### model_plot(frame: ndarray, results1: Results | None = None, results2: Results | None = None, results3: Results | None = None)

识别碰撞箱绘制函数，使用全部模型检测时，需要根据各模型结果对原始图像进行各自的碰撞箱绘制
:param frame: 传入的原始图像
:type frame: np.ndarray
:param results1: 火焰识别模型的识别结果，如果为None，则不绘制
:type results1: Results
:param results2: 人像识别模型的识别结果，如果为None，则不绘制
:type results2: Results
:param results3: 异常行为识别模型的识别结果，如果为None，则不绘制

* **返回:**
  **frame** – 绘制各碰撞箱后的结果图像
* **返回类型:**
  np.ndarray

#### predict(pre_source: str | ndarray, mode: int | None = None, show: int | None = None, iou: float | None = None, conf: float | None = None)

模型预测函数，可以根据mode选择模型加载图片/视频进行预测，获得对应的返回结果
允许mode为0，此时会调用所有模型进行识别，保存得到三个结果对象序列，使用字典将其与对应的模式进行映射

* **参数:**
  * **pre_source** (*Union* *[**str* *,* *np.ndarray* *]*) – 用于推理的的特定数据源，可以是矩阵，图片路径，URL，视频路径或者设备id
    支持广泛的格式和来源，实现了跨不同类型输入的灵活应用。
  * **mode** (*int*) – 指定使用的识别模型，未指定(为None)时使用内部的默认模式对应的模型进行识别
  * **show** (*bool*) – 指定模型的预测结果是否可视化，未指定(为None)时使用默认值
  * **iou** (*float*) – 指定衡量预测边界框与真实边界框之间重叠程度，未指定(为None)时使用默认值
  * **conf** (*float*) – 指定模型对识别设置的置信度阈值，未指定(为None)时使用默认值
* **返回:**
  **result_dict** – 由模式-yolov8内置的结果对象序列组成你的字典，每个元素为一个模型-Result对象序列的键值对
  通过访问对应模式对应的值，可以获得识别结果的各项信息
* **返回类型:**
  Optional[dict[int, list[Results]]]

#### predict_class_type_color_dict *= {1: {0: (0, 0, 255), 1: (128, 128, 128)}, 2: (0, 255, 0), 3: (255, 0, 0)}*

noindex:

#### re_detect(video_file: str, ui_event=None, mode: int | None = None, save_dir: str | None = None, max_frame: int | None = None, iou: float | None = None, sensitivity: int = 0)

对传入视频路径的视频的检测和处理函数，是视频检测器的另一个核心处理函数
被创建后作为独立的进程运行，不受视频处理器的创建进程影响，只受ui界面的停止命令影响
:param video_file: 要处理视频的指定绝对路径
:type video_file: str
:param ui_event: 用于监听ui界面的停止信息的事件
:type ui_event: multiprocessing.Event
:param mode: 指定的模式，用户指定后由视频流处理器传给当前的检测器实例，以完成用户要求的检测功能
:type mode: int
:param save_dir: 指定的视频保存路径，目前不提供设置方式，需要在进一步优化后完成设置
:type save_dir: str
:param max_frame: 指定的最大缓冲区帧数，因为无法直接解析视频设备的帧率，故暂未用于实践
:type max_frame: int
:param iou: 指定衡量预测边界框与真实边界框之间重叠程度，未指定(为None)时使用默认值
:type iou: float
:param sensitivity: 指定对异常的敏感程度，0对应低敏感程度，设置置信度阈值为0.6，1对应高敏感程度，设置置信度阈值为0.5，默认为低敏感
:type sensitivity: int

#### reset_training_parameters(batch: int | None = None, epochs: int | None = None, project: str | None = None, name: str | None = None, imgsz: int | None = None, data: str | None = None, weight_pt: str | None = None, device: int | None = None)

重新设置模型训练时使用的参数，仅修改传入的参数，其他参数不变

* **参数:**
  * **batch** (*int*) – 每次训练时输入的图片数量，默认为16
  * **epochs** (*int*) – 训练迭代的次数，默认为5
  * **project** (*str*) – 训练文件存放的目录，默认在根目录下的train_file文件夹下
  * **name** (*str*) – 训练过程存放的文件，在project对应目录下创建子目录，存储训练的日志和输出结果
  * **imgsz** (*int*) – 输入图片的尺寸，默认要求640\*640
  * **data** (*str*) – 有关数据集配置文件的路径，由于本项目目标主要是对火焰的识别，在yolov8下默认存放的是fire.yaml
    其默认路径为：ultralytics/cfg/datasets
    在该配置文件内按yolov8格式设置好训练集、验证集、测试集的图片路径，类别名等参数
  * **weight_pt** (*str*) – 预训练模型的文件名，可用于用户自行完成训练任务，当其不存在时yolov8会自动下载
  * **device** (*int*) – 可用设备的编号，此处主要用于设置CPU

#### set_default_model(mode: int)

设置默认使用模型
:param mode: 0设置使用全部模型，1设置使用火焰模型，2设置使用人像识别模型，3设置异常行为识别模型
:type mode: int

#### show_csv()

对训练完成后的各种评估参数绘制图像

#### train()

火焰识别模型的训练
需要在类外设置好训练参数和配置文件，以及数据集

#### warning_mode_list *= [1, 2, 4, 8]*

noindex:

## home_security_surveillance.Video_process.video_processor module

File Name: video_processor.py
Author: 07xiaohei
Date: 2024-05-13
Version: 1.5
Description: 处理视频流的核心类

### *class* home_security_surveillance.Video_process.video_processor.Video_Processor(url_capture_time_out, root)

基类：`object`

从视频源处获得视频流并进行处理的相关类，是家庭监控系统的核心处理部分

* **参数:**
  * **url_capture_time_out** (*int*) – opencv在捕捉网络摄像头url视频流时的超时时间设置，各协议统一，且应小于opencv已设置的时间
    此处最大为15s，默认值为10s，最大请尽量小于15s
  * **event** (*synchronize.Event*) – ui界面创建对象时传递的事件，在该类传递事件内标记设置为False时结束任务退出进程，默认为None
  * **return_value** (*multiprocessing.Value*) – ui界面创建对象时传递的共享内存变量，默认为None

#### ui_event

ui界面创建对象时传递的事件，在该类传递事件内标记设置为False时结束任务退出进程，默认为None

* **Type:**
  synchronize.Event

#### ui_value

ui界面创建对象时传递的共享内存变量，默认为None

* **Type:**
  multiprocessing.Value

#### create_time

创建该对象的时间，字符串类型，格式与log.py中Log_Processor的strftime_all相同

* **Type:**
  str

#### url_capture_time_out

opencv在捕捉网络摄像头url视频流时的超时时间设置，各协议统一，且应小于opencv已设置的时间
此处最大为15s，默认值为10s，最大请尽量小于15s

* **Type:**
  int

#### config_data

配置文件的字典格式，每个元素为一个键值对，键为配置文件的属性名，值为配置文件的属性值

* **Type:**
  dict

#### local_video_device_list

关于本地视频设备的一个列表，每个元素为一个元组，每个元组内有两个子元素
每个元组的第一个元素是视频源的相关信息作为show_video_in_cv函数的输入，用于opencv库从视频源中获得视频流
每个元组的第二个元素是视频源的相关说明

* **Type:**
  List[ Tuple[ Union[int,str],str ] ]

#### logger

日志处理器对象的一个实例，用于记录该类活动过程中的运行信息和错误信息

* **Type:**
  [Log_Processor](home_security_surveillance.File_process.md#home_security_surveillance.File_process.log.Log_Processor)

#### nvd_processor

网络视频设备处理器对象的一个实例，用于处理网络应用设备的加载、访问和修改

* **Type:**
  Nvd_processor

#### hs_processor

历史视频处理器对象的一个实例，用于处理对历史视频的加载、访问和识别

* **Type:**
  History_video_processor

#### video_detector

视频检测处理器对象的一个实例，使用基于yolov8的识别模型对视频流进行监测

* **Type:**
  [Video_Detector](#home_security_surveillance.Video_process.video_detect.Video_Detector)

#### warning_processor

异常警报处理器对象的一个实例，使用smtplib库发送邮件，pygame库播放音频，tkinter库弹出警告窗口

* **Type:**
  Warning_processor

#### \_load_flag

标记上述的本地视频设备、网络视频设备和历史视频处理器的加载是否成功且不为空，便于后续处理时确定是否可用

* **Type:**
  List[bool, bool, bool]

### 备注

视频流的来源包括本地视频设备(如USB摄像头)，网络视频设备（如ip摄像头）和历史监控视频三种
传入video_type=1对应本地监视器设备，video_type=2对应网络视频设备，video_type=3对应历史监控视频

### 示例

#### load_history_video(video_strat_save_date: str, video_index: int = 1, flag_visibility: bool = True, flag_re_detect: bool = True, video_detect_sensitivity: int = 0, video_detect_type: int = 1)

从历史视频保存文件夹中利用opencv库加载视频流，根据传入的视频录制日期和索引号来捕捉视频信息

* **参数:**
  * **video_strat_save_date** (*str*) – 要加载的历史视频的保存日期，跨日的视频以开始保存的日期为准，用于opencv库从视频源处获得视频流
    注意日期的格式为{年}分隔符{月}分隔符{日}，年一定是长为4的字符串
  * **video_index** (*int*) – 要加载的历史视频在保存日期的索引，用于区别单个日期保存的多个视频，默认为第一个，即索引为1
  * **flag_visibility** (*bool*) – 控制opencv在读取视频流时是否展示，True时展示视频，False时不展示，可用于后台处理视频
  * **flag_re_detect** (*bool*) – 控制历史视频是否需要进行监测，目标追踪，默认为True
  * **video_detect_sensitivity** (*int*) – 控制视频流在监测时的敏感度，0为低敏感度，1为高敏感度
  * **video_detect_type** (*int*) – 控制历史视频监测的类型，0为全部监测，1为只监测火焰，2为只监测人，3为检测异常情况
* **返回:**
  **res** – 返回一个整型，每个值对应一个错误类型或者正确类型
  0则说明读取、展示、识别成功
  -1则说明视频流打开失败(如视频实际是一个txt文件)
  -2则说明视频流意外关闭(如加载视频到一半被手动删除)
  1说明历史保存视频为空
  2说明要加载视频的日期无视频
  3说明索引不存在
* **返回类型:**
  int

#### load_local_video_device(video_sourse: int = 0, flag_visibility: bool = True, flag_save: bool = True, flag_detect: bool = True, video_detect_type: int = 1, video_detect_sensitivity: int = 0)

从本地视频设备利用opencv库加载视频流，根据传入的本地视频设备号来捕捉视频信息

* **参数:**
  * **video_sourse** (*int*) – 要捕获的本地视频设备的索引号，用于opencv库从视频源处获得视频流
  * **flag_visibility** (*bool*) – 控制opencv在读取视频流时是否展示，True时展示视频，False时不展示，可用于后台处理视频
  * **flag_save** (*bool*) – 控制opencv在读取视频六时是否保存，True时保存视频，False时不保存
  * **flag_detect** (*bool*) – 控制视频流是否需要进行监测，目标追踪，默认为True
  * **video_detect_type** (*int*) – 控制视频流监测的类型，0为全部监测，1为只监测火焰，2为只监测人，3为检测异常情况
  * **video_detect_sensitivity** (*int*) – 控制视频流在监测时的敏感度，0为低敏感度，1为高敏感度
* **返回:**
  **res** – 返回一个整型，每个值对应一个错误类型或者正确类型
  0则说明读取、展示和保存成功
  -1则说明打开摄像头失败
  -2则说明读取摄像头下一帧失败或者摄像头意外关闭
  -3则说明指定保存视频文件时，创建目录或打开视频文件失败
  1说明本地视频设备为空
  2说明传入索引号超过了本地视频设备列表大小
* **返回类型:**
  int

### 备注

为了加速模型识别处理速度，创建一个进程单独执行识别功能，与该进程的通信使用两个多进程队列multiprocessing.Queue
一个是frame_queue，用于将捕捉的视频帧在处理后传给识别进程
一个是result_queue，用于将识别进程识别到错误的获得的错误类型和置信度返回给该进程

#### load_network_video_device(video_sourse: int | str = 0, flag_visibility: bool = True, flag_save: bool = True, flag_detect: bool = True, video_detect_type: int = 1, video_detect_sensitivity: int = 0, video_protocol_type: str = 'RTSP')

从网络视频设备利用opencv库加载视频流，根据传入的url、ip或者已存储url的索引值来捕捉视频信息

* **参数:**
  * **video_sourse** (*Union* *[**int* *,* *str* *]*) – 传入的ip或者url字符串，或者是已存储url的索引值
  * **flag_visibility** (*bool*) – 控制opencv在读取视频流时是否展示，True时展示视频，False时不展示，可用于后台处理视频
  * **flag_save** (*bool*) – 控制opencv在读取视频流时是否保存，True时保存视频，False时不保存
  * **flag_detect** (*bool*) – 控制视频流是否需要进行监测，目标追踪，默认为True
  * **video_detect_type** (*int*) – 控制视频流监测的类型，0为全部监测，1为只监测火焰，2为只监测人，3为检测异常情况
  * **video_detect_sensitivity** (*int*) – 控制视频流在监测时的敏感度，0为低敏感度，1为高敏感度
  * **video_protocol_type** (*str*) – 读取视频流时网络视频设备使用的传输协议，默认为RSTP
* **返回:**
  **res** – 返回一个整型，每个值对应一个错误类型或者正确类型
  0则说明读取、展示和保存成功
  -1则说明打开摄像头失败
  -2则说明读取摄像头下一帧失败或者摄像头意外关闭
  -3则说明指定保存视频文件时，创建目录或打开视频文件失败
  1则说明网络视频设备为空
  2则说明网络设备视频传输协议不支持
  3则说明无法从url处获得视频流，即VideoCapture超时，与打开摄像头失败不同
* **返回类型:**
  int

#### load_video_sourse()

加载视频资源函数

#### update_local_video_sourse()

更新本地视频设备
:returns: **flag** – 是否完成了更新，如更新返回True，否则为False
:rtype: bool

## Module contents
