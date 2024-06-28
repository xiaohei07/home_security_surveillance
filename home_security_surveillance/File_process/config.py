# -*- coding: utf-8 -*-
"""
File Name: config.py
Author: 07xiaohei
Date: 2024-05-10
Version: 1.5
Description: config配置文件的处理部分
"""
import home_security_surveillance.frozen_dir
# 引用常用库
from home_security_surveillance.Common import *
from home_security_surveillance.frozen_dir import project_dir
__all__ = ["config_file", "config_keys", "config_defaluts", "trans_config_abspath",
           "write_config", "load_config"]

## 变量部分 ##

# 配置文件的默认路径
config_file = os.path.normpath(
    os.path.join(project_dir, "./Config/config.json"))

# config文件可用的键值
config_keys = \
    [
        "exception-monitoring-directory", "history-video-directory",
        "IP-video-device-file", "log-directory", "model-directory"
    ]

# config文件的默认键值对
config_defaluts = \
    {
        "history-video-directory": "History_video",
        "IP-video-device-file": "Config/IP_video_device.json",
        "model-directory": "Model",
        "log-directory": "Logs",
        "exception-monitoring-directory": "Exception_monitoring"
    }


## 方法部分 ##

def trans_config_abspath(relative_path: Union[Dict[str, str], List[str], str]
                         ) -> Union[Dict[str, str], List[str], str]:
    """
    由于配置文件中的路径默认只有名称，需要转化为绝对路径
    如果是绝对路径不做修改
    将默认配置文件的相对路径转化为绝对路径

    Parameters
    ----------
    relative_path : Union[Dict[str,str], List[str], str]
        传入的相对路径，可以是单个的，也可以是一个字典或者列表

    Returns
    -------
    abs_path : Union[Dict[str, str], List[str], str]
        将相应的相对路径转化为绝对路径的结果
    """
    # 深拷贝
    rel_path = copy.deepcopy(relative_path)
    # 类型检验
    if not isinstance(rel_path, (str, dict, list)):
        raise TypeError("relative path should be of type str, list, or dict.")

    # 相对路径转换
    # 从该代码文件的路径变为项目根路径
    root_path = project_dir
    if isinstance(rel_path, str):
        if not os.path.isabs(rel_path):
            return os.path.normpath(os.path.join(root_path, rel_path))
    if isinstance(rel_path, list):
        for i in range(len(rel_path)):
            if not os.path.isabs(rel_path[i]):
                rel_path[i] = os.path.normpath(os.path.join(root_path, rel_path[i]))
        return rel_path
    if isinstance(rel_path, dict):
        for key, value in rel_path.items():
            if not os.path.isabs(value):
                rel_path[key] = os.path.normpath(os.path.join(root_path, value))
        return rel_path


def _generate_defalut_config():
    """
    在默认位置写入默认配置文件
    """
    with open(config_file, 'w') as file:
        json.dump(config_defaluts, file,
                  skipkeys=False, check_circular=True, allow_nan=True, sort_keys=False,
                  ensure_ascii=False, separators=(',', ' : '), indent=2)
    return


def _write_config(config_data: Dict[str, str]):
    """
    将字典形式的配置信息写入配置文件函数
    Parameters
    ----------
    config_data : Dict[str, str]
        要写入配置文件的配置键值对全部内容，均为字符串，视为内部函数，不提供外部接口
    """
    # 检查每个键值对是否为字符串
    for key, value in config_data.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise TypeError("Config data dictionary items type muse be string!")

    # 检查每个键是否符合要求
    for key in config_data.keys():
        if key not in config_keys:
            raise ValueError(f"The {key} key is not in config keys!")

    with open(config_file, 'w', encoding='utf-8') as file:
        json.dump(config_data, file,
                  skipkeys=False, check_circular=True, allow_nan=True, sort_keys=False,
                  ensure_ascii=False, separators=(',', ' : '), indent=2)


def write_config(json_key: str, json_value: str):
    """
    将单个键值对的配置信息写入配置文件函数
    可用于添加或修改，但仅限于已有的部分

    Parameters
    ----------
    json_key : str
        要写入配置文件的单个键
    json_value :str
        要写入配置文件的单个值
    """
    # 检查键值对是否为字符串
    if not isinstance(json_key, str) or not isinstance(json_value, str):
        raise TypeError("Config data dictionary items type muse be string!")
    # 检查键是否符合要求
    if json_key not in config_keys:
        raise ValueError(f"The {json_key} key is not in config keys!")

    # 加载已有配置文件，不转化为绝对路径，完成修改
    config_data, _ = load_config(relative=True)
    config_data[json_key] = json_value
    _write_config(config_data)


def load_config(relative: bool = False) -> Tuple[dict, dict]:
    """
    加载配置文件函数

    Parameters
    ----------
    relative : bool
        控制返回时字典型配置文件的文件路径是相对的还是绝对的，默认为绝对

    Returns
    -------
    config_data : dict
        返回从json格式文件中加载的字典型配置文件,如无可用的键值自动用默认键值对补充
    invalid_config_data : dict
        返回json格式文件中的无效键值对,无内容时为{}
    """

    config_data = config_defaluts
    invalid_config_data = {}
    # 打开配置文件
    with open(config_file, 'r', encoding='utf-8') as file:
        try:
            # 加载配置文件内容
            config_data.update(json.load(file))
            # 获得无效键值对并删除
            for key, value in config_data.items():
                if key not in config_keys:
                    invalid_config_data[key] = value
            for del_key in invalid_config_data.keys():
                del config_data[del_key]
        # 加载出错时抛出错误，需要修改错误信息，将文件名信息加入其中
        except json.decoder.JSONDecodeError as e:
            new_e_msg = f"Error decoding JSON in file '{file}': {e.msg}"
            raise json.decoder.JSONDecodeError(new_e_msg, e.doc, e.pos) from e

    # 如果有无效内容，重新写入正确的配置文件
    if invalid_config_data:
        _write_config(config_data)

    # 重写后检验每个配置路径是否存在
    for value in trans_config_abspath(config_data).values():
        if not os.path.exists(value):
            raise ValueError(f"The {value} path is not exist!")
    if relative:
        return config_data, invalid_config_data
    else:
        return trans_config_abspath(config_data), invalid_config_data


## 模块单元测试部分，调用部分方法，保证文件内所有方法均已被调用 ##
if __name__ == "__main__":

    # 测试绝对路径，可用键值和默认键值对变量内容
    print(config_file,config_keys,config_defaluts,sep='\n')

    # 测试转化相对路径的结果
    print(trans_config_abspath(config_defaluts))

    # 测试写入默认内容到配置文件
    _generate_defalut_config()

    # 测试加载配置文件
    print(load_config()[0])

    # 测试写入不存在的键
    write_config("xxx","yyy")

    # 测试修改不存在文件
    write_config(config_keys[0],"zzz")
    print(load_config(relative = True)[0])
