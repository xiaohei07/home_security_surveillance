# home_security_surveillance.Exception_process package

## Submodules

## home_security_surveillance.Exception_process.Warning_Processor module

File Name: Warning_Processor.py
Author: Chai.h
Date: 2024-05-22
Version: 1.5
Description: 发出异常警报的相关处理

### *class* home_security_surveillance.Exception_process.Warning_Processor.Warning_Processor(warning_dir, user_email)

基类：`object`

异常警报处理器，与发出异常警报相关
负责根据模型预测模块的结果生成警报、通知用户或相关部门，并执行相关的应急响应措施。
该模块通过实时传递警报信息，帮助用户和管理者及时响应各类异常情况
主要实现四个场景的警报：
1. 火灾警报
2. 烟雾警报
3. 人体识别（陌生人警报）
4. 跌倒警报

* **参数:**
  **warning_dir** (*str*) – 警告日志文件存放的文件夹，默认值和_config_defaluts中exception-monitoring-directory的对应绝对路径相同

#### \_email_senter_config_keys

邮件发送者配置文件可用的键值，包括email、password、name、domain和tld，是类变量

* **Type:**
  List[str]

email_smtp_address_dict
: 常用邮件服务运营商的Smtp邮箱地址和端口

warning_code_dict
: 错误编码字典，0001对应烟雾，0010对应火焰，0100对应陌生人，1000对应跌倒异常行为
  不同的组合对应多种错误的出现，如0110代表同时出现了火焰、陌生人的错误

warning_dir
: 警告日志文件存放的文件夹

warning_logger
: 日志处理器对象的一个实例，用于记录该类活动过程中的运行信息和警告信息

email_senter_file
: 邮件发送者的配置文件路径

email_senter_data
: 邮箱发送者的email相关信息，每个元素包括email、password、username、domain、tld的键值对

email_receiver_file
: 邮件接收者的配置文件路径

email_receiver_data
: 邮箱接收者的email相关信息，每个元素为邮件接收者的地址字符串

#### append_email_receiver(email_receiver_address: str)

添加邮件接收者函数
:param email_receiver_address: 邮件接收者函数地址
:type email_receiver_address: str

* **返回:**
  **flag** – 是否添加成功
* **返回类型:**
  bool

#### append_email_senter(email_senter_address: str, email_senter_password)

添加邮件发送者函数，作为最新值使用
:param email_senter_address: 邮件发送者邮件地址
:type email_senter_address: str
:param email_senter_password: 邮件发送者邮件密码
:type email_senter_password: str

* **返回:**
  **flag** – 是否添加成功
* **返回类型:**
  bool

#### delete_email_receiver(email_receiver_address: str)

删除邮件接收者函数
:param email_receiver_address: 邮件接收者函数地址
:type email_receiver_address: str

* **返回:**
  **flag** – 是否添加成功
* **返回类型:**
  bool

#### email_smtp_address_dict *= {'126': ('smtp.126.com', '25'), '139': ('smtp.139.com', '25'), '163': ('smtp.163.com', '994'), 'foxmail': ('SMTP.foxmail.com', '25'), 'gmail': ('smtp.gmail.com', '587'), 'qq': ('smtp.qq.com', '587')}*

#### *static* get_level_description(level: float, sensitivity: int = 0)

根据置信度判断危险等级，返回置信度级别描述函数

* **参数:**
  * **level** (*float*) – 置信度，数值在 0 ~ 1 之间
  * **sensitivity** (*int*) – 置信度转换为危险等级时使用的不同敏感度，0为低敏感度，1为高敏感度
* **返回:**
  **level_description** – 对置信度危险等级的描述，返回一个整型数，是根据置信度的大判断的危险等级：
  如果是高敏感度：
  > 0.5以下认为置信度不够，默认无危险
  > 0.5~0.6表示危险性不大，危险等级为1
  > 0.6~0.7中等危险，又可能会发生事故，危险等级为2
  > 0.7~0.8大概率识别出事故，并且判断较为准确，危险等级为3
  > 0.8~1 极度危险状态，危险等级为4

  如果是低敏感度：
  : 0.6以下认为误识别的风险高于识别风险，默认无危险
    0.6~0.7表示危险性不大，危险等级为1
    0.7~0.8中等危险，又可能会发生事故，危险等级为2
    0.8~0.9大概率识别出事故，并且判断较为准确，危险等级为3
    0.9~1 极度危险状态，危险等级为4
* **返回类型:**
  int

#### load_email_receiver_config(email_receiver: str)

加载邮件发送者配置文件为对应的数据结构
:param email_receiver: 要加载的邮件接收者配置文件的路径
:type email_receiver: str

* **返回:**
  **email_receiver_data** – 邮件接收者文件解析所得数据，是一个字符串列表，每个元素对应一个邮件接收者地址字符串
* **返回类型:**
  List[str]

#### load_email_senter_config(email_senter: str, re_parse: bool = True)

加载邮件发送者配置文件为对应的数据结构

* **参数:**
  * **email_senter** (*str*) – 要加载的邮件发送者配置文件的路径
  * **re_parse** (*bool*) – 是否重新解析email的内容，默认为True
* **返回:**
  **email_senter_data** – 邮件发送者文件中json列表的第一个字典的解析所得数据，每个元素对应一个存储邮件发送者相关信息的字符串
* **返回类型:**
  Dict[str, str]

#### send_email_notification(warning_type: str, warning_time: str, level_description: int)

发送邮件通知用户发生了相应的紧急事故函数

* **参数:**
  * **warning_type** (*str*) – 警告类型文本
  * **warning_time** (*str*) – 警告时间文本
  * **level_description** (*int*) – 置信度危险等级

#### show_custom_warning_dialog(warning_type: str, warning_time: str, level_description: int)

桌面跳出警报窗口函数

* **参数:**
  * **warning_type** (*str*) – 警告类型文本
  * **warning_time** (*str*) – 警告时间文本
  * **level_description** (*int*) – 置信度危险等级

#### *static* slice_email(email: str)

邮件地址切片函数
:param email: 传入的电子邮件地址
:type email: str

* **返回:**
  **email_parts** – 邮件的各个部分，username属性对应邮件名，domain属性对应域名，tld属性对应顶级域名
* **返回类型:**
  Dict[str, str]

#### trigger_warning(warning_type: str, warning_time: str, level: float, sensitivity: int)

触发警报的核心处理函数

* **参数:**
  * **warning_type** (*str*) – 警告类型文本，根据传递的参数判断事故发生的类型，做出不同的处理
  * **warning_time** (*str*) – 警告时间文本，说明事故发生的时间
  * **level** (*float*) – 置信度，根据数值的大小判断危险等级，给出不同提示（图标显示和提示音）
    当危险等级高于等于3级时，会向户主发送邮件，通知相关情况
  * **sensitivity** (*int*) – 置信度转换为危险等级时使用的不同敏感度，0为低敏感度，1为高敏感度

#### warning_code_dict *= {1: 'Smoke', 2: 'Fire', 4: 'Stranger', 8: 'Person-Falling'}*

#### warning_process(warning_code: int, warning_time: str, level_list: List[float], sensitivity: int = 0)

错误处理的核心函数

* **参数:**
  * **warning_code** (*int*) – 映射所得的错误编码
  * **warning_time** (*str*) – 警告时间文本，说明事故发生的时间
  * **level_list** (*List* *[**float* *]*) – 置信度列表，每个元素为对应错误的置信度
  * **sensitivity** (*int*) – 置信度转换为危险等级时使用的不同敏感度，0为低敏感度，1为高敏感度

## Module contents
