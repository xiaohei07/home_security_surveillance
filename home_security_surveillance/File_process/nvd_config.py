# -*- coding: utf-8 -*-
"""
File Name: nvd_config.py
Author: 07xiaohei
Date: 2024-05-10
Version: 1.0
Description: nvd文件的处理，nvd是网络视频设备(network_video_device)的简写，一般为网络摄像头
"""

# 引入常用库
from home_security_surveillance.Common import *
# 引入config模块获得默认文件位置
from home_security_surveillance.File_process.config import config_defaluts, trans_config_abspath
# 引入urllib.parse库的urlparse函数用于解析从url中解析得到相关信息
from urllib.parse import urlparse
# 引入ipaddress库，检验ip是否合理
from ipaddress import ip_address

__all__ = ["Nvd_Processor"]

# 当前代码文件路径
_nvd_config_code_file = __file__

class Nvd_Processor(object):
    """
    Nvd_Processor(nvd_config_file, re_parse)
    网络视频设备处理器对象，用于处理网络应用设备的json文件和数据结构

    Parameters
    ----------
    nvd_config_file : str
        要加载的网络摄像头配置文件的路径，默认值和_config_defaluts中的IP-video-device-file对应绝对路径相同
    re_parse : bool
        是否重新解析url的内容，默认为True

    Attributes
    ----------
    _nvd_config_keys : List[str, ...]
        nvd配置文件可用的键值，包括url、index、ip、port、username和passname，是类变量
    _nvd_config_defaluts : Dict[str, str]
        nvd配置文件的默认键值对，是类变量
    nvd_config_data : List[Dict[str, str]]
        网络摄像头配置文件中解析所得数据，包含了网络视频设备(IP摄像头)的url、ip等信息
        是一个json列表，每个元素对应一个存储网络摄像头相关信息的字典对象
    video_trans_protocol_dict: Dict[int, str]
        网络摄像头传输视频使用的协议，是类变量
        包括大部分网络摄像头使用的传输协议，key为索引，value为对应的协议字符串
    Notes
    -----

    Examples
    --------
    """

    # nvd配置文件可用的键值
    _nvd_config_keys = \
        [
            "url", "index", "ip", "port", "username", "password"
        ]
    # nvd配置文件的默认键值对
    _nvd_config_defaluts = \
        {
            "url": "No-url",
            "index": -1,
            "ip": "No-ip",
            "port": "No-port",
            "username": "No-username",
            "password": "No-password"
        }

    # 网络摄像头传输视频使用的协议
    # 1为http、2为https、3为rtsp、4为rtmp
    video_trans_protocol_dict = {1: "http://", 2: "https://", 3: "rtsp://", 4: "rtmp://"}

    def __init__(self, nvd_config_file: str = trans_config_abspath(config_defaluts["IP-video-device-file"]),
                 re_parse: bool = True):
        """初始化网络视频设备处理器对象"""

        # 保存配置文件路径
        self.nvd_config_file = nvd_config_file
        # 加载配置文件，保存为对应的数据结构
        self.nvd_config_data = self.load_nvd_config(nvd_config_file, re_parse)
        # 由于可能进行了解析，需要向配置文件写入解析结果
        self._write_nvd_config()

    def _write_nvd_config(self, nvd_config_data: List[Dict[str, str]] = []):
        """
        将传入的网络视频设备的数据写入网络摄像头配置文件，视为内部函数，不提供外部接口
        Parameters
        ----------
        nvd_config_data : List[Dict[str, str]]
            传入的网络视频设备的数据，默认为空，此时重写使用的是类内的nvd_config_data
        """

        # 空则写入类的nvd_config_data，否则写入nvd_config_data
        if not nvd_config_data:
            with open(self.nvd_config_file, 'w', encoding='utf-8') as file:
                json.dump(self.nvd_config_data, file,
                          skipkeys=False, check_circular=True, allow_nan=True, sort_keys=False,
                          ensure_ascii=False, separators=(',', ' : '), indent=2)
        else:
            with open(self.nvd_config_file, 'w', encoding='utf-8') as file:
                json.dump(nvd_config_data, file,
                          skipkeys=False, check_circular=True, allow_nan=True, sort_keys=False,
                          ensure_ascii=False, separators=(',', ' : '), indent=2)

    def change_nvd_config(self, nvd_config_data: List[Dict[str, str]] = []):
        """修改网络视频设备的配置文件内容，和写入函数的参数相同"""
        self._write_nvd_config(nvd_config_data)

    def load_nvd_config(self, nvd_config_file: str, re_parse: bool = True) \
            -> List[Dict[str, str]]:
        """
        加载nvd配置文件为对应的数据结构
        Parameters
        ----------
        nvd_config_file : str
            要加载的网络摄像头配置文件的路径
        re_parse : bool
            是否重新解析url的内容，默认为True
        Returns
        -------
        nvd_config_data : List[Dict[str, str]]
            网络摄像头配置文件中解析所得数据，是一个json列表，每个元素对应一个存储网络摄像头相关信息的字典对象
        """

        # 打开文件进行加载，加载的错误在调用处进行处理
        with open(nvd_config_file, 'r', encoding='utf-8') as file:
            # 加载网络摄像头配置文件内容
            nvd_config_data = json.load(file)
            # 如果只有一个字典，转为列表
            if isinstance(nvd_config_data, dict):
                nvd_config_data = [nvd_config_data]

            # 加载后判断其是否只有url键值，如果存在没有的键值，解析url并赋值内容到其中
            # 如果设置了重新解析，对url的内容进行直接解析
            if re_parse:
                index = 1
                for i in nvd_config_data:
                    # 根据当前顺序重新索引
                    i["index"] = index
                    index += 1
                    # 解析url并赋值
                    parsed_url = urlparse(i["url"])
                    if parsed_url.hostname is not None:
                        i["ip"] = parsed_url.hostname
                    else:
                        i["ip"] = self._nvd_config_defaluts["ip"]
                    if parsed_url.port is not None:
                        i["port"] = str(parsed_url.port)
                    else:
                        i["port"] = self._nvd_config_defaluts["port"]
                    if parsed_url.username is not None:
                        i["username"] = parsed_url.username
                    else:
                        i["username"] = self._nvd_config_defaluts["username"]
                    if parsed_url.password is not None:
                        i["password"] = parsed_url.password
                    else:
                        i["password"] = self._nvd_config_defaluts["password"]

            # 如果未设置，仅当只有url元素时进行解析，以获得url相应信息
            else:
                index = 1
                for i in nvd_config_data:
                    # 获得没有的键值
                    missing_keys = set(self._nvd_config_keys) - set(i.keys())
                    # 检查是否有存在url但没有键值的情况
                    if i["url"] != self._nvd_config_defaluts["url"] and \
                            missing_keys:

                        # 为其创建索引
                        if "index" in missing_keys:
                            i["index"] = index
                        elif i["index"] == -1:
                            i["index"] = index

                        # 解析url，将没有键值的内容赋值到其中
                        parsed_url = urlparse(i["url"])
                        if parsed_url.hostname is not None and "ip" in missing_keys:
                            i["ip"] = parsed_url.hostname
                        else:
                            i["ip"] = self._nvd_config_defaluts["ip"]
                        if parsed_url.port is not None and "port" in missing_keys:
                            i["port"] = str(parsed_url.port)
                        else:
                            i["port"] = self._nvd_config_defaluts["port"]
                        if parsed_url.username is not None and "username" in missing_keys:
                            i["username"] = parsed_url.username
                        else:
                            i["username"] = self._nvd_config_defaluts["username"]
                        if parsed_url.password is not None and "password" in missing_keys:
                            i["password"] = parsed_url.password
                        else:
                            i["password"] = self._nvd_config_defaluts["password"]
                    index += 1

        return nvd_config_data

    def add_nvd_config(self, nvd_url: str):
        """
        添加网络设备ip
        Parameters
        ----------
        nvd_url : str
            网络视频设备的url地址
        """
        # 类型检验
        if not isinstance(nvd_url, str):
            raise TypeError("Network video device muse be string!")

        # 添加新url，增加索引并解析获得、ip、port、username、password
        add_nvd_dict = {"url": nvd_url}

        new_index = len(self.nvd_config_data) + 1
        add_nvd_dict["index"] = new_index

        parsed_url = urlparse(nvd_url)
        if parsed_url.hostname is not None:
            add_nvd_dict["ip"] = parsed_url.hostname
        else:
            add_nvd_dict["ip"] = self._nvd_config_defaluts["ip"]
        if parsed_url.port is not None:
            add_nvd_dict["port"] = str(parsed_url.port)
        else:
            add_nvd_dict["port"] = self._nvd_config_defaluts["port"]
        if parsed_url.username is not None:
            add_nvd_dict["username"] = parsed_url.username
        else:
            add_nvd_dict["username"] = self._nvd_config_defaluts["username"]
        if parsed_url.password is not None:
            add_nvd_dict["password"] = parsed_url.password
        else:
            add_nvd_dict["password"] = self._nvd_config_defaluts["password"]

        # 保存解析结果，更新nvd_config_data结构
        self.nvd_config_data.append(add_nvd_dict)
        # 将更新后结果写入到配置文件中
        self._write_nvd_config()

    def delete_nvd_config(self, del_information: Union[str, int]):
        """
        删除某个不使用的网络视频设备
        Parameters
        ----------
        del_information : Union[str, int]
            要删除设备的url或者索引
        """

        # 根据类型确定是url或者是索引并进行删除
        if isinstance(del_information, str):
            for i in range(len(self.nvd_config_data)):
                if self.nvd_config_data[i]["url"] == del_information:
                    del self.nvd_config_data[i]
                    break
        else:
            for i in range(len(self.nvd_config_data)):
                if self.nvd_config_data[i]["index"] == del_information:
                    del self.nvd_config_data[i]
                    break
        self._write_nvd_config()

    @staticmethod
    def vaild_ip(ip: str) -> int:
        """
        判断是否是ip，并检验ip是否合理
        Parameters
        ----------
        ip : str
            输入的ip地址
        Returns
        -------
        type : int
            传入字符串是否是ip，0表示不是ip，1表示是ipv4,2表示是ipv6
        """
        # 解析IP地址
        try:
            ip_obj = ip_address(ip)
            # 检查IP地址类型并返回相应结果
            if ip_obj.version == 4:
                return 4
            elif ip_obj.version == 6:
                return 6
        except ValueError:
            return 0

    def from_ip_find_url(self, ip: str) -> str:
        """
        查找是否有此ip地址，并返回url
        Parameters
        ----------
        ip : str
            传入的ip地址
        Returns
        -------
        url : str
            返回ip对应的url，如果不存在该ip，返回空字符串
        """
        for i in self.nvd_config_data:
            if i["ip"] == ip:
                return i["url"]
        return ""

    def vaild_protocol(self, video_type: str) -> int:
        """
        # 验证要使用的协议是否可用，并返回对应的索引
        Parameters
        ----------
        video_type : str
            摄像头使用协议的字符串
        Returns
        -------
            video_trans_protocol_dict中对应协议的索引
        """
        # 小写传入字符串
        video_type = video_type.lower()
        for i in self.video_trans_protocol_dict.items():
            # 如果找到了协议，返回对应索引
            if video_type in i[1]:
                return i[0]
        # 否则返回0
        return 0

# 模块测试部分
if __name__ == "__main__":
    # 测试加载网络视频设备配置文件
    nvd_processor = Nvd_Processor(re_parse=False)
    print(nvd_processor.nvd_config_data)
    print()

    # 增加网络视频设备配置文件的测试
    nvd_processor.add_nvd_config("http://10.197.97.225:4747/")
    print(nvd_processor.nvd_config_data)
    print()

    # 修改网络视频设备配置文件的测试
    nvd_processor.nvd_config_data[2]["ip"] = "123:123:9:9"
    nvd_processor.change_nvd_config()
    print(nvd_processor.nvd_config_data)
    print()

    # 删除网络视频设备配置文件的测试
    nvd_processor.delete_nvd_config("http://10.197.97.225:4747/")
    print(nvd_processor.nvd_config_data)
    print()

    # 验证ip
    print(nvd_processor.vaild_ip("aaa:bb:c:dd"))
    print(nvd_processor.vaild_ip("10.197.97.224"))
    print(nvd_processor.vaild_ip("10.197.97.274"))
    print(nvd_processor.vaild_ip("FC00:0000:130F:0000:0000:09C0:876A:130B"))
    print(nvd_processor.vaild_ip("FC00:0:130F:0000:0000:09C0:876A:130B"))
    print(nvd_processor.vaild_ip("FC00:0:ZZZZ:0000:0000:09C0:876A:130B"))

    # 查找ip对应的url
    print(nvd_processor.from_ip_find_url("10.197.97.274"))
    print(nvd_processor.from_ip_find_url("10.197.97.224"))

    # 协议验证
    print(nvd_processor.vaild_protocol("Http"))
    print(nvd_processor.vaild_protocol("RTSP"))
    print(nvd_processor.vaild_protocol("xxxx"))