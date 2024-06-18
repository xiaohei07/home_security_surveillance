# -*- coding: utf-8 -*-
"""
File Name: history_video.py
Author: 07xiaohei
Date: 2024-05-12
Version: 1.0
Description: 对历史视频记录文件的处理部分
"""

# 引用常用库
from home_security_surveillance.Common import *
# 引入config模块获得默认目录位置
from home_security_surveillance.File_process.config import config_defaluts, trans_config_abspath

__all__ = ["History_Video_Processor"]

class History_Video_Processor(object):
    """
    History_Video_Processor(hv_dir)
    历史视频处理器对象，用于处理历史视频目录内的目录和文件，以及对应的数据结构

    Parameters
    ----------
    hv_dir : str
        历史视频文件的根目录，默认值和_config_defaluts中的history-video-directory对应绝对路径相同
    video_suffix : str
        保存历史视频文件时的默认后缀，默认为"avi"

    Attributes
    ----------
    hv_root_dir : str
        历史视频文件的根目录，和hv_dir相同
    hv_dict : Dict[str, Dict[int, Tuple[str, str]]]
        历史视频文件索引字典，第一级是年月日格式的字符串，
        第二级是一个字典，key为视频文件的索引，value为一个元组，第一个元素是视频文件绝对路径，第二个元素是视频开始时间
        年月日格式是格式化后的，索引是整型
    video_suffix : str
        保存历史视频文件时的默认后缀，保存是统一的
    Notes
    -----
    历史视频目录的结构和命名格式为:
    第一级目录，命名格式为：年-月
    |   第二级目录，命名格式为：日
    |   |  不同的历史视频文件：命名格式为"视频索引值"+"_"+_strftime_date格式的开始时间.{video_suffix}"
    数据结构的存储和实际目录有所区别(前者为了便于处理，后者为了便于外部寻找)
    Examples
    --------
    """

    def __init__(self, hv_dir: str = trans_config_abspath(config_defaluts["history-video-directory"]),
                 video_suffix: str = "avi"):
        """初始化历史视频处理器对象"""
        # 保存根目录和视频后缀
        self.hv_root_dir = hv_dir
        self.video_suffix = video_suffix
        # 存储根目录下的视频文件信息，此处说明了格式
        self.hv_dict: Dict[str, Dict[int, Tuple[str, str]]] = {}

        # 读取历史视频目录，对应年-月
        for first_level_dir in os.listdir(hv_dir):
            first_level_dir_path = os.path.join(hv_dir, first_level_dir)
            if os.path.isdir(first_level_dir_path):

                # 读取历史视频子目录，对应日
                for sencond_level_dir in os.listdir(first_level_dir_path):
                    second_level_dir_path = os.path.join(first_level_dir_path, sencond_level_dir)
                    if os.path.isdir(second_level_dir_path):

                        # 组合得到日期
                        date_str = self.date_build(first_level_dir, sencond_level_dir)
                        self.hv_dict[date_str] = {}

                        # 保存对应日期的视频文件信息字典，元素以索引为键，值为视频文件绝对路径和开始时间字符串组成的元组
                        for third_level_file in os.listdir(second_level_dir_path):
                            video_path = os.path.join(second_level_dir_path, third_level_file)
                            if os.path.isfile(video_path):
                                index, time_str = self.parse_history_video_name(third_level_file)
                                self.hv_dict[date_str][index] = (video_path, time_str)

        # 无视频文件时删除空字典对应的元素，防止出现错误
        self.hv_dict = {key: value for key, value in self.hv_dict.items() if value}

    @staticmethod
    def parse_date(date_str: str, split: str = "-") -> Tuple[int, int, int]:
        """
        类的静态方法，用于将年-月-日或其他分割格式的日期转为年月日的三元素元组
        Parameters
        ----------
        date_str : str
            传入的日期字符串，包含年月日信息
        split : str
            传入的日期分隔符，默认为"-"
        Returns
        -------
        date_tuple : Tuple[int, int, int]
            返回年月日的三元素元组，默认类型为int
        """

        # 使用指定的分割符号分割字符串
        date_list = date_str.split(split)
        # 将分割后的结果转换为整数，并构建日期元组
        date_tuple = tuple(map(int, date_list))
        return date_tuple  # type: ignore

    @staticmethod
    def format_date(date_tuple: Tuple[int, int, int]) -> str:
        """
        类的静态方法，用于将年月日的三元素元组转为年-月-日格式的日期

        Parameters
        ----------
        date_tuple : Tuple[int, int, int]
            年月日的三元素元组
        Returns
        -------
        date_str : str
            年-月-日格式的日期
        """
        # 将元组解构为年、月、日
        year, month, day = date_tuple
        # 使用字符串格式化将日期转换为字符串
        date_str = f"{year}-{month:02d}-{day:02d}"
        return date_str

    @staticmethod
    def date_build(year_month_str: str, day_str: str, split: str = "-") -> str:
        """
        根据年月和日拼接得到日期
        Parameters
        ----------
        year_month_str : str
            年-月或其他分割格式的年份月份信息
        day_str : str
            日期信息
        split : str
            年份月份字符串的分割符,默认为"-"
        Returns
        -------
        date_str : str
            年-月-日或其他分割格式的日期信息
        """
        # 拼接日期并返回结果
        date_str = f"{year_month_str}{split}{int(day_str):02d}"
        # 格式化拼接日期并返回结果
        date_tuple = History_Video_Processor.parse_date(date_str, split)
        date_str = History_Video_Processor.format_date(date_tuple)  # type: ignore
        return date_str

    @staticmethod
    def date_split(date_str: str, split: str = "-") -> Tuple[str, str]:
        """
        将日期格式字符串转为年月字符串和日字符串
        Parameters
        ----------
        date_str : str
            年-月-日或其他分割格式的日期信息
        split : str
            年份月份字符串的分割符,默认为"-"
        Returns
        -------
        year_month_str : str
            年-月或其他分割格式的年份月份信息
        day_str : str
            日期信息
        """
        # 格式化日期字符串
        date_str = History_Video_Processor.format_date(
            History_Video_Processor.parse_date(date_str, split))  # type: ignore

        # 将格式化后日期字符串分割为年、月和日
        year_str, month_str, day_str = date_str.split(split)

        # 返回年月字符串和日字符串
        return f"{year_str}-{month_str}", day_str

    @staticmethod
    def parse_time(time_str: str, split: str = "-") -> Tuple[int, int, int]:
        """
        类的静态方法，用于将时-分-秒或其他分割格式的时间转为时分秒的三元素元组
        Parameters
        ----------
        time_str : str
            传入的时间字符串，包含时分秒信息
        split : str
            传入的时间分隔符，默认为"-"
        Returns
        -------
        time_tuple : Tuple[int, int, int]
            返回时分秒的三元素元组，默认类型为int
        """
        # 直接使用日期格式的解析即可
        return History_Video_Processor.parse_date(time_str, split)  # type: ignore

    @staticmethod
    def format_time(time_tuple: Tuple[int, int, int]) -> str:
        """
        类的静态方法，用于将时分秒的三元素元组转为时-分-秒格式的时间

        Parameters
        ----------
        time_tuple : Tuple[int, int, int]
            时分秒的三元素元组
        Returns
        -------
        time_str : str
            时分秒格式的时间
        """
        # 将元组解构为时、分、秒
        hour, minute, second = time_tuple
        # 使用字符串格式化将日期转换为字符串
        time_str = f"{hour:02d}-{minute:02d}-{second:02d}"
        return time_str

    @staticmethod
    def parse_history_video_name(name_str: str) -> Tuple[int, str]:
        """
        类的静态方法，用于解析视频文件名为合适的数据结构
        Parameters
        ----------
        name_str : 视频文件名的字符串

        Returns
        -------
        index, start_time_str : Tuple[int, str]
            存储了包含视频索引和开始时间的字符串
        """
        index, start_time_str = name_str.split("_")
        index = int(index)
        start_time_str, _ = start_time_str.split(".")
        return index, start_time_str

    def _generate_new_index(self, date_str: str) -> int:
        """
        根据传入日期生成一个新的视频索引，如本日之前已有保存的视频，则需要生成最新保存视频索引+1的新索引
        该日期无保存视频时从1开始生成
        Parameters
        ----------
        date_str : str
            已格式化的传入的日期信息，与hv_dict格式内容相同
        Returns
        -------
        new_index : int
            传入日期的最新视频索引
        """
        new_index = 1
        # 如果加载时该日无保存视频，索引为1
        if date_str not in self.hv_dict:
            return new_index
        # 否则索引为最新值
        else:
            new_index = max(self.hv_dict[date_str].keys()) + 1
            return new_index

    def generate_video_file(self, start_time: str) -> str:
        """
        根据传入的开始时间生成历史视频文件路径
        Parameters
        ----------
        start_time : str
            视频开始保存的时间，格式与Log_processor.strftime_all相同
        Returns
        -------
        new_video_file : str
            根据当前文件夹情况和开始时间生成的新文件路径(未创建文件)，用于保存视频文件
        """
        # 分割得到日期字符串和时间字符串
        date_str, time_str = start_time.split("_")
        # 格式化日期和时间字符串
        date_str = self.format_date(self.parse_date(date_str))  # type: ignore
        time_str = self.format_time(self.parse_time(time_str))  # type: ignore

        # 根据日期获得新的索引
        new_index = self._generate_new_index(date_str)
        # 分割日期字符串
        year_month_str, day_str = self.date_split(date_str)

        # 根据年月字符串和日字符串创建目录/定位到已有目录
        video_dir = os.path.join(self.hv_root_dir, year_month_str, day_str)
        # new_index为1，说明该日期未存储过视频
        if new_index == 1:
            # 创建视频文件目录，错误信息在调用该函数的地方处理
            os.makedirs(video_dir, exist_ok=True)

        # 设置视频文件名
        new_video_file = os.path.join(video_dir, f"{new_index}_{time_str}.{self.video_suffix}")

        # 创建目录无问题/路径无错误，更新hv_dict
        # 如果该日期非空
        if self.hv_dict.get(date_str) is not None:
            self.hv_dict[date_str][new_index] = time_str
        # 为空，创建字典，保存新索引为键，新文件绝对路径和开始时间字符串组成的元组为值
        else:
            self.hv_dict[date_str] = {}
            self.hv_dict[date_str][new_index] = (new_video_file, time_str)

        # 返回生成的文件路径
        return new_video_file

    def delete_new_video_file(self, del_video_file: str):
        """
        外部创建视频文件失败后，在历史视频处理器中的删除函数
        Parameters
        ----------
        del_video_file : str
            根据当前文件夹情况和开始时间生成的最终文件路径，传入该参数说明创建文件失败
        """
        # 提取文件路径中的年月、日信息
        video_dir = os.path.split(del_video_file)[0]
        year_moth_dir, day_str = os.path.split(video_dir)
        year_month_str = os.path.split(year_moth_dir)[1]
        # 提取文件名中的索引信息
        index = int(os.path.basename(del_video_file).split("_")[0])

        # 根据年月和日拼接得到日期
        date_str = self.date_build(year_month_str, day_str)

        # 利用日期和索引信息删除指定元素
        del self.hv_dict[date_str][index]

        # 如果日期已空，删除日期键值对
        if not self.hv_dict[date_str]:
            del self.hv_dict[date_str]

    def _vaild_video_file(self, video_strat_save_date: str, video_index: int) -> int:
        """
        通过hv_dict验证视频文件视频存在函数
        Parameters
        ----------
        video_strat_save_date : str
            要加载的历史视频的保存日期，跨日的视频以开始保存的日期为准，用于opencv库从视频源处获得视频流
            注意日期的格式为{年}分隔符{月}分隔符{日}，年一定是长为4的字符串
        video_index : int
            要加载的历史视频在保存日期的索引，用于区别单个日期保存的多个视频

        Returns
        -------
        video_exist : int
            视频文件是否存在，1代表存在，2代表该日期无视频文件，3代表该索引不存在
        """

        # 解析传入日期，再格式化日期为统一的格式，分隔符默认为第五个字符，即年份之后的第一个字符
        video_strat_save_date = self.format_date(
            self.parse_date(video_strat_save_date, video_strat_save_date[4]))  # type: ignore

        # 获得该日期的所有视频
        date_dict = self.hv_dict.get(video_strat_save_date)
        # 检查日期，如果日期不存在，返回对应结果
        if date_dict is None:
            return 2
        # 否则检查传入索引号是否存在，如果索引号不存在，返回对应结果
        elif date_dict.get(video_index) is None:
            return 3
        # 否则存在
        else:
            return 1

    def get_video_file(self, video_strat_save_date: str, video_index: int) \
            -> Tuple[str, Union[str, int]]:
        """
        通过hv_dict获得对应日期和索引的视频文件函数
        Parameters
        ----------
        video_strat_save_date : str
            要加载的历史视频的保存日期，跨日的视频以开始保存的日期为准，用于opencv库从视频源处获得视频流
            注意日期的格式为{年}分隔符{月}分隔符{日}，年一定是长为4的字符串
        video_index : int
            要加载的历史视频在保存日期的索引，用于区别单个日期保存的多个视频

        Returns
        -------
        video_save_file : str
            视频文件存在时，返回其保存的字符串路径，否则，返回空字符串
        video_information : Union[str, int]
            视频文件存在时，返回视频文件的对应信息字符串，格式为:年-月-日_索引_时-分-秒，包括了时间信息和索引信息
            如果日期不存在，返回2，如果索引不存在，返回3
        """

        # 通过hv_dict验证是否视频文件是否存在
        video_exist = self._vaild_video_file(video_strat_save_date, video_index)

        # 不存在则返回错误值
        if video_exist != 1:
            return "", video_exist

        # 存在将参数转换为路径
        else:
            # 解析传入日期，再格式化日期为统一的格式，分隔符默认为第五个字符，即年份之后的第一个字符
            video_strat_save_date = self.format_date(
                self.parse_date(video_strat_save_date, video_strat_save_date[4]))  # type: ignore

            # 获得保存的视频文件绝对路径
            video_save_file = self.hv_dict[video_strat_save_date][video_index][0]
            # 生成文件信息，包括视频保存开始时间
            video_information = f"{video_strat_save_date}_{video_index}_" \
                                f"{self.hv_dict[video_strat_save_date][video_index][1]}"
            # 返回路径和信息
            return video_save_file, video_information

    def get_date_video_file(self, video_strat_save_date: str) \
            -> Tuple[Dict[int, str], Union[Dict[int, str], int]]:
        """
        通过hv_dict获得对应日期的视频文件字典和视频文件信息字典函数
        Parameters
        ----------
        video_strat_save_date : str
            保存的视频的对应日期，格式为年-月-日，跨日的视频以开始保存的日期为准
        Returns
        -------
        video_file_list : Dict[int, str]
            视频日期存在时，返回其每个视频的索引，字符串路径组成的键值对的，否则，返回空字典
        video_information_list : Union[Dict[int, str], int]
            视频文件存在时，返回每个视频文件的对应信息字符串列表，格式为:年-月-日_索引_时-分-秒，包括了时间信息和索引信息
            如果日期不存在，返回2，如果无视频文件，返回3
        """
        # 解析传入日期，再格式化日期为统一的格式，分隔符默认为第五个字符，即年份之后的第一个字符
        video_strat_save_date = self.format_date(
            self.parse_date(video_strat_save_date, video_strat_save_date[4]))  # type: ignore

        # 获得该日期的所有视频
        date_dict = self.hv_dict.get(video_strat_save_date)

        # 如果不存在，返回空字典和错误类型2
        if date_dict is None:
            return {}, 2
        # 如果是空字典，返回空字典和错误类型3
        if not date_dict:
            return {}, 3

        # 否则保存获得对应日期的视频文件字典和视频文件信息字典

        # 保存索引+文件路径和索引+文件信息结果的字典
        video_file_dict = {}
        video_information_dict = {}

        # 遍历，保存每个存在索引的对应的路径和文件信息
        for i in date_dict.keys():
            video_save_file, video_information = self.get_video_file(video_strat_save_date, i)
            video_file_dict[i] = video_save_file
            video_information_dict[i] = video_information
        # 返回结果
        return video_file_dict, video_information_dict

# 模块测试部分
if __name__ == "__main__":
    hs_processor = History_Video_Processor()
    # 解析目录结果
    print(hs_processor.hv_dict)

    # 时间转化,parse_time用于将字符串转为元组
    # hs_processor.hv_dict["2021-10-01"]获得的是字典
    # 可以根据视频索引访问字典以获得对应的开始时间
    print(hs_processor.parse_time(
        hs_processor.hv_dict["2021-10-01"][1][1]))

    # 格式化日期和时间
    print(hs_processor.format_date((2024, 5, 12)))
    print(hs_processor.format_date((20, 15, 30)))

    # 分割日期为年月和日
    print(hs_processor.date_split("2024-5-12"))

    # 根据当前时间生成新的视频文件路径
    res = hs_processor.generate_video_file(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    print(res)
    print(hs_processor.hv_dict)

    # 删除生成的视频文件路径
    hs_processor.delete_new_video_file(res)
    print(hs_processor.hv_dict)

    # 根据传入日期和索引获得视频文件路径，并验证
    video_file, video_info = hs_processor.get_video_file("2024-06-11", 1)
    res = cv.VideoCapture(video_file)
    print(res.isOpened())
    print(video_info)
    print(hs_processor.get_video_file("2024-06-12", 1))
    print(hs_processor.get_video_file("2024-06-11", 100))

    # 获得传入日期的全部视频文件
    video_file_list, video_information_list = hs_processor.get_date_video_file("2024-06-11")
    print(video_file_list)
    print(video_information_list)
    print(hs_processor.get_date_video_file("2024-06-12"))
    