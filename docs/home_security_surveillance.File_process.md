# home_security_surveillance.File_process package

## Submodules

## home_security_surveillance.File_process.config module

File Name: config.py
Author: 07xiaohei
Date: 2024-05-10
Version: 1.5
Description: config配置文件的处理部分

### home_security_surveillance.File_process.config.load_config(relative: bool = False)

加载配置文件函数

* **参数:**
  **relative** (*bool*) – 控制返回时字典型配置文件的文件路径是相对的还是绝对的，默认为绝对
* **返回:**
  * **config_data** (*dict*) – 返回从json格式文件中加载的字典型配置文件,如无可用的键值自动用默认键值对补充
  * **invalid_config_data** (*dict*) – 返回json格式文件中的无效键值对,无内容时为{}

### home_security_surveillance.File_process.config.trans_config_abspath(relative_path: Dict[str, str] | List[str] | str)

由于配置文件中的路径默认只有名称，需要转化为绝对路径
如果是绝对路径不做修改
将默认配置文件的相对路径转化为绝对路径

* **参数:**
  **relative_path** (*Union* *[**Dict* *[**str* *,**str* *]* *,* *List* *[**str* *]* *,* *str* *]*) – 传入的相对路径，可以是单个的，也可以是一个字典或者列表
* **返回:**
  **abs_path** – 将相应的相对路径转化为绝对路径的结果
* **返回类型:**
  Union[Dict[str, str], List[str], str]

### home_security_surveillance.File_process.config.write_config(json_key: str, json_value: str)

将单个键值对的配置信息写入配置文件函数
可用于添加或修改，但仅限于已有的部分

* **参数:**
  * **json_key** (*str*) – 要写入配置文件的单个键
  * **json_value** (*str*) – 要写入配置文件的单个值

## home_security_surveillance.File_process.history_video module

File Name: history_video.py
Author: 07xiaohei
Date: 2024-05-12
Version: 1.5
Description: 对历史视频记录文件的处理部分

### *class* home_security_surveillance.File_process.history_video.History_Video_Processor(hv_dir)

基类：`object`

历史视频处理器对象，用于处理历史视频目录内的目录和文件，以及对应的数据结构

* **参数:**
  * **hv_dir** (*str*) – 历史视频文件的根目录，默认值和_config_defaluts中的history-video-directory对应绝对路径相同
  * **video_suffix** (*str*) – 保存历史视频文件时的默认后缀，默认为”avi”

#### hv_root_dir

历史视频文件的根目录，和hv_dir相同

* **Type:**
  str

#### hv_dict

历史视频文件索引字典，第一级是年月日格式的字符串，
第二级是一个字典，key为视频文件的索引，value为一个元组，第一个元素是视频文件绝对路径，第二个元素是视频开始时间
年月日格式是格式化后的，索引是整型

* **Type:**
  Dict[str, Dict[int, Tuple[str, str]]]

#### video_suffix

保存历史视频文件时的默认后缀，保存是统一的

* **Type:**
  str

### 备注

历史视频目录的结构和命名格式为:
第一级目录，命名格式为：年-月
|   第二级目录，命名格式为：日
|   |  不同的历史视频文件：命名格式为”视频索引值”+”_”+_strftime_date格式的开始时间.{video_suffix}”
数据结构的存储和实际目录有所区别(前者为了便于处理，后者为了便于外部寻找)

### 示例

#### *static* date_build(year_month_str: str, day_str: str, split: str = '-')

根据年月和日拼接得到日期

* **参数:**
  * **year_month_str** (*str*) – 年-月或其他分割格式的年份月份信息
  * **day_str** (*str*) – 日期信息
  * **split** (*str*) – 年份月份字符串的分割符,默认为”-”
* **返回:**
  **date_str** – 年-月-日或其他分割格式的日期信息
* **返回类型:**
  str

#### *static* date_split(date_str: str, split: str = '-')

将日期格式字符串转为年月字符串和日字符串

* **参数:**
  * **date_str** (*str*) – 年-月-日或其他分割格式的日期信息
  * **split** (*str*) – 年份月份字符串的分割符,默认为”-”
* **返回:**
  * **year_month_str** (*str*) – 年-月或其他分割格式的年份月份信息
  * **day_str** (*str*) – 日期信息

#### delete_new_video_file(del_video_file: str)

外部创建视频文件失败后，在历史视频处理器中的删除函数

* **参数:**
  **del_video_file** (*str*) – 根据当前文件夹情况和开始时间生成的最终文件路径，传入该参数说明创建文件失败

#### *static* format_date(date_tuple: Tuple[int, int, int])

类的静态方法，用于将年月日的三元素元组转为年-月-日格式的日期

* **参数:**
  **date_tuple** (*Tuple* *[**int* *,* *int* *,* *int* *]*) – 年月日的三元素元组
* **返回:**
  **date_str** – 年-月-日格式的日期
* **返回类型:**
  str

#### *static* format_time(time_tuple: Tuple[int, int, int])

类的静态方法，用于将时分秒的三元素元组转为时-分-秒格式的时间

* **参数:**
  **time_tuple** (*Tuple* *[**int* *,* *int* *,* *int* *]*) – 时分秒的三元素元组
* **返回:**
  **time_str** – 时分秒格式的时间
* **返回类型:**
  str

#### generate_video_file(start_time: str)

根据传入的开始时间生成历史视频文件路径

* **参数:**
  **start_time** (*str*) – 视频开始保存的时间，格式与Log_processor.strftime_all相同
* **返回:**
  **new_video_file** – 根据当前文件夹情况和开始时间生成的新文件路径(未创建文件)，用于保存视频文件
* **返回类型:**
  str

#### get_date_video_file(video_strat_save_date: str)

通过hv_dict获得对应日期的视频文件字典和视频文件信息字典函数

* **参数:**
  **video_strat_save_date** (*str*) – 保存的视频的对应日期，格式为年-月-日，跨日的视频以开始保存的日期为准
* **返回:**
  * **video_file_list** (*Dict[int, str]*) – 视频日期存在时，返回其每个视频的索引，字符串路径组成的键值对的，否则，返回空字典
  * **video_information_list** (*Union[Dict[int, str], int]*) – 视频文件存在时，返回每个视频文件的对应信息字符串列表，格式为:年-月-日_索引_时-分-秒，包括了时间信息和索引信息
    如果日期不存在，返回2，如果无视频文件，返回3

#### get_video_file(video_strat_save_date: str, video_index: int)

通过hv_dict获得对应日期和索引的视频文件函数

* **参数:**
  * **video_strat_save_date** (*str*) – 要加载的历史视频的保存日期，跨日的视频以开始保存的日期为准，用于opencv库从视频源处获得视频流
    注意日期的格式为{年}分隔符{月}分隔符{日}，年一定是长为4的字符串
  * **video_index** (*int*) – 要加载的历史视频在保存日期的索引，用于区别单个日期保存的多个视频
* **返回:**
  * **video_save_file** (*str*) – 视频文件存在时，返回其保存的字符串路径，否则，返回空字符串
  * **video_information** (*Union[str, int]*) – 视频文件存在时，返回视频文件的对应信息字符串，格式为:年-月-日_索引_时-分-秒，包括了时间信息和索引信息
    如果日期不存在，返回2，如果索引不存在，返回3

#### *static* parse_date(date_str: str, split: str = '-')

类的静态方法，用于将年-月-日或其他分割格式的日期转为年月日的三元素元组

* **参数:**
  * **date_str** (*str*) – 传入的日期字符串，包含年月日信息
  * **split** (*str*) – 传入的日期分隔符，默认为”-”
* **返回:**
  **date_tuple** – 返回年月日的三元素元组，默认类型为int
* **返回类型:**
  Tuple[int, int, int]

#### *static* parse_history_video_name(name_str: str)

类的静态方法，用于解析视频文件名为合适的数据结构

* **参数:**
  **name_str** ( *视频文件名的字符串*)
* **返回:**
  **index, start_time_str** – 存储了包含视频索引和开始时间的字符串
* **返回类型:**
  Tuple[int, str]

#### *static* parse_time(time_str: str, split: str = '-')

类的静态方法，用于将时-分-秒或其他分割格式的时间转为时分秒的三元素元组

* **参数:**
  * **time_str** (*str*) – 传入的时间字符串，包含时分秒信息
  * **split** (*str*) – 传入的时间分隔符，默认为”-”
* **返回:**
  **time_tuple** – 返回时分秒的三元素元组，默认类型为int
* **返回类型:**
  Tuple[int, int, int]

## home_security_surveillance.File_process.log module

File Name: log.py
Author: 07xiaohei
Date: 2024-05-10
Version: 1.5
Description: nvd文件的处理，nvd是网络视频设备(network_video_device)的简写，一般为网络摄像头

### *class* home_security_surveillance.File_process.log.Log_Processor(log_dir, log_name, level)

基类：`object`

日志处理器对象，用于创建日志文件并进行读写

* **参数:**
  * **log_dir** (*str*) – 日志的根目录
  * **log_name** (*str*) – 日志的文件名
  * **level** (*int*) – 数字形式的日志优先级，默认为INFO级别

#### strftime_all

日志文件记录时间的格式，是类变量

* **Type:**
  str

#### strftime_date

日志文件记录日期的格式，是类变量

* **Type:**
  str

#### strftime_time

日志文件记录时分秒的格式，是类变量

* **Type:**
  str

### CRITICAL = logging.CRITICAL

日志文件输出的消息级别，致命错误

### ERROR = logging.ERROR

日志文件输出的消息级别，一般错误

### WARNING = logging.WARNING

日志文件输出的消息级别，警告

### INFO = logging.INFO

日志文件输出的消息级别，日常事务

### DEBUG = logging.DEBUG

日志文件输出的消息级别，调试过程

#### logger

日志记录器对象的一个实例，用于记录活动过程中的运行信息和错误信息

* **Type:**
  Logger

### 备注

对要使用的Logger的包装

### 示例

#### CRITICAL *= 50*

#### *class* CustomFormatter(fmt=None, datefmt=None, style='%', validate=True)

基类：`Formatter`

#### format(record)

Format the specified record as text.

The record’s attribute dictionary is used as the operand to a
string formatting operation which yields the returned string.
Before formatting the dictionary, a couple of preparatory steps
are carried out. The message attribute of the record is computed
using LogRecord.getMessage(). If the formatting string uses the
time (as determined by a call to usesTime(), formatTime() is
called to format the event time. If there is exception information,
it is formatted using formatException() and appended to the message.

#### DEBUG *= 10*

#### ERROR *= 40*

#### INFO *= 20*

#### WARNING *= 30*

#### log_write(content: str | Exception, level: int)

* **参数:**
  * **content** (*Union* *[**str* *,* *Exception* *]*) – 写入日志的信息，可以是错误类型，也可以是字符串
  * **level** (*int*) – 写入日志的级别，包括CRITICAL、ERROR、WARNING、INFO、DEBUG五个级别

#### strftime_all *= '%Y-%m-%d_%H-%M-%S'*

#### strftime_date *= '%Y-%m-%d'*

noindex:

#### strftime_time *= '%H-%M-%S'*

noindex:

## home_security_surveillance.File_process.nvd_config module

File Name: nvd_config.py
Author: 07xiaohei
Date: 2024-05-10
Version: 1.5
Description: nvd文件的处理，nvd是网络视频设备(network_video_device)的简写，一般为网络摄像头

### *class* home_security_surveillance.File_process.nvd_config.Nvd_Processor(nvd_config_file, re_parse)

基类：`object`

网络视频设备处理器对象，用于处理网络应用设备的json文件和数据结构

* **参数:**
  * **nvd_config_file** (*str*) – 要加载的网络摄像头配置文件的路径，默认值和_config_defaluts中的IP-video-device-file对应绝对路径相同
  * **re_parse** (*bool*) – 是否重新解析url的内容，默认为True

#### \_nvd_config_keys

nvd配置文件可用的键值，包括url、index、ip、port、username和passname，是类变量

* **Type:**
  List[str, …]

#### \_nvd_config_defaluts

nvd配置文件的默认键值对，是类变量

* **Type:**
  Dict[str, str]

#### nvd_config_data

网络摄像头配置文件中解析所得数据，包含了网络视频设备(IP摄像头)的url、ip等信息
是一个json列表，每个元素对应一个存储网络摄像头相关信息的字典对象

* **Type:**
  List[Dict[str, str]]

#### video_trans_protocol_dict

网络摄像头传输视频使用的协议，是类变量
包括大部分网络摄像头使用的传输协议，key为索引，value为对应的协议字符串

* **Type:**
  Dict[int, str]

### 备注

### 示例

#### add_nvd_config(nvd_url: str)

添加网络设备ip
:param nvd_url: 网络视频设备的url地址
:type nvd_url: str

#### change_nvd_config(nvd_config_data: List[Dict[str, str]] = [])

修改网络视频设备的配置文件内容，和写入函数的参数相同

#### delete_nvd_config(del_information: str | int)

删除某个不使用的网络视频设备
:param del_information: 要删除设备的url或者索引
:type del_information: Union[str, int]

#### from_ip_find_url(ip: str)

查找是否有此ip地址，并返回url
:param ip: 传入的ip地址
:type ip: str

* **返回:**
  **url** – 返回ip对应的url，如果不存在该ip，返回空字符串
* **返回类型:**
  str

#### load_nvd_config(nvd_config_file: str, re_parse: bool = True)

加载nvd配置文件为对应的数据结构
:param nvd_config_file: 要加载的网络摄像头配置文件的路径
:type nvd_config_file: str
:param re_parse: 是否重新解析url的内容，默认为True
:type re_parse: bool

* **返回:**
  **nvd_config_data** – 网络摄像头配置文件中解析所得数据，是一个json列表，每个元素对应一个存储网络摄像头相关信息的字典对象
* **返回类型:**
  List[Dict[str, str]]

#### *static* vaild_ip(ip: str)

判断是否是ip，并检验ip是否合理
:param ip: 输入的ip地址
:type ip: str

* **返回:**
  **type** – 传入字符串是否是ip，0表示不是ip，1表示是ipv4,2表示是ipv6
* **返回类型:**
  int

#### vaild_protocol(video_type: str)

# 验证要使用的协议是否可用，并返回对应的索引
:param video_type: 摄像头使用协议的字符串
:type video_type: str

* **返回类型:**
  video_trans_protocol_dict中对应协议的索引

#### video_trans_protocol_dict *= {1: 'http://', 2: 'https://', 3: 'rtsp://', 4: 'rtmp://'}*

noindex:

## Module contents
