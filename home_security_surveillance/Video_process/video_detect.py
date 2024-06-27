# -*- coding: utf-8 -*-
"""
File Name: video_detect.py
Author: youyou
Date: 2024-05-02
Version: 1.5
Description: 使用yolov8，对视频帧进行识别，判断监控是否出现了火灾/人/异常行为
"""

# 引入常用库
from home_security_surveillance.Common import *
# 用日志处理器
from home_security_surveillance.File_process.log import *
# 用config模块获得默认目录位置
from home_security_surveillance.File_process.config import config_defaluts, trans_config_abspath
# 用Warning_Processor模块
from home_security_surveillance.Exception_process import *
from home_security_surveillance.frozen_dir import project_dir
# 用torch
import torch
# 用yolo类
from ultralytics import YOLO
# 用Results类
from ultralytics.engine.results import Results
# 用csv类
import csv
# 用plt绘出csv结果图
import matplotlib.pyplot as plt
# 双端队列做缓冲
from collections import deque
import IPython

__all__ = ["Video_Detector"]

# 训练和预测配置文件的默认路径
defalut_train_config_path = os.path.normpath(
    os.path.join(project_dir, "./Model/train_config.json"))

defalut_predict_config_path = os.path.normpath(
    os.path.join(project_dir, "./Model/predict_config.json"))

class Video_Detector(object):
    """
    Video_Detector(root_dir, use_defalut_parameter)
    视频检测处理器，用于读取部分实时帧完成对应任务的识别功能，是自动检测和识别的核心模块
    使用的底层架构为yolov8，火焰模型为自行利用数据集训练，人像识别和异常行为识别直接使用开源模型

    Parameters
    ----------
    root_dir : str
        视频检测处理器的根目录，默认值和_config_defaluts中的model-directory对应绝对路径相同
    use_defalut_parameter : bool
        是否使用默认的内置训练参数，否则需要加载配置文件的对应参数，True为使用内置参数，False为不使用

    Attributes
    ----------
    root_dir : str
        视频检测处理器的根目录，默认值和_config_defaluts中的model-directory对应绝对路径相同
    info_logger & error_logger: Log_Processor
        日志处理器对象的实例，分别用于记录该类活动过程中的运行和错误、报警信息，统一输入到根目录下的info.log和error.log中
    _train_config & _predict_config: dict
        train_config和predict_config配置文件中的各变量记录，在后续加载时使用，是内部成员，不对外开放接口
    device : int
        标识用户可用于的识别的设备，如果有独显GPU使用独显GPU，否则使用CPU
    train_model : YOLO
        被用于训练的预加载模型，仅在训练新模型时使用
    predict_model: dict[int, YOLO]
        模式-模型的数字-模型对象字典映射，通过映射可以将模式转变为yolov8要使用的模型对象，直接进行预测
        此成员用于加速处理，保证多次调用预测函数或者修改模型内容时，均需要在初始化时加载一次模型即可

    model_mode_dict : dict[int, str]
        模式-模型的数字-绝对路径字典映射，通过映射可以将模式转变为yolov8要使用的模型绝对路径
        其将相对路径和根路径改为绝对路径，路径根目录用root_dir
        1为火焰模型，2为人物模型 3：火焰和人物模型
    warning_mode_list : list[int]
        类变量，预测类型和错误码的匹配关系，在检测时需要进行进程的通信，遇到错误需要向视频流处理器通知错误的出现
        因此需要将各类型的错误统一映射为一个错误码，视频流处理器通过解码即可获知错误类型
    mode_precdict_class : dict[int, dict[int, int]]
        类变量，将使用的mode和预测类别映射为对应的类型，即将映射的错误码1248分别修改为0123
    mode_precdict_warning_mode : dict[int, dict[int, int]]
        类变量，将使用的模型mode和预测类别映射为错误码
        mode=1对应第一个火焰/烟雾模型，1的预测类别是烟雾，对应错误码是1
        0的预测类别是火焰，对应错误码是2，mode=2对应第二个人像识别模型，0的预测类别是人，对应错误码是4
        mode=3对应第三个异常行为识别，0的预测类别是跌倒，对应错误码是8
    predict_class_type_color_dict : dict[int, dict[int, int]]
        类变量，每个错误类型在绘制错误碰撞箱时使用的颜色，只在使用全部模型模式下有效
        第一个键值model对应的mode，第二个键值是预测所得的类型，值为它们的对应颜色

    ## 训练参数属性集合 ##
    batch: int          每次训练时输入的图片数量，默认为16
    epochs: int         训练迭代的次数，默认为5
    project: str        训练文件存放的目录，默认在根目录下的train_file文件夹下
    name: str           训练过程存放的文件，在project对应目录下创建子目录，存储训练的日志和输出结果
    imgsz: int          输入图片的尺寸，默认要求640*640
    data: str           有关数据集配置文件的路径，由于本项目目标主要是对火焰的识别，在yolov8下默认存放的是fire.yaml
                        其默认路径为：ultralytics/cfg/datasets
                        在该配置文件内按yolov8格式设置好训练集、验证集、测试集的图片路径，类别名等参数
    weight_pt: str      预训练模型的文件名，可用于用户自行完成训练任务，当其不存在时yolov8会自动下载

    ## 预测参数属性集合 ##
    model_mode: int     当用户未指定使用模型时，进行预测默认使用的模式，默认为1，即火焰识别
    iou: float          衡量预测边界框与真实边界框之间重叠程度，用于移除重叠较大的多余边界框，保留最优的检测结果，默认为0.6
    conf: float         模型对识别设置的置信度阈值，低于该阈值的识别结果会被过滤，默认为0.5
    show: bool          模型的预测结果是否可视化，在单独调用模型内部预测函数时可以用来展示结果，默认为True
    save_dir: str       模型预测结果的保存目录，可在其中查看预测获得的识别信息视频和图片
    max_frame: int      从视频流处理器处获得视频帧时，存储的双端队列最大缓冲视频帧数量
                        考虑到大多数摄像头是30帧左右，默认存储1800帧，即保存一分钟左右的视频，可用于保存视频，获知异常出现的前因后果
    Notes
    -----
    获取相关参数(可以让用户选择模式)，前端通过修改predict_config.json中的model_mode来改变模式
    配置文件的参数都可以和用户进行交互
    """

    #: :noindex:
    mode_precdict_warning_mode = {1: {0: 2, 1: 1}, 2: {0: 4}, 3: {0: 8}}
    #: :noindex:
    mode_precdict_class = {1: {0: 1, 1: 0}, 2: {0: 2}, 3: {0: 3}}
    #: :noindex:
    warning_mode_list = [1, 2, 4, 8]
    #: :noindex:
    predict_class_type_color_dict = {1: {0: (0, 0, 255), 1: (128, 128, 128)},
                                     2: (0, 255, 0), 3: (255, 0, 0)}

    def __init__(self, root_dir: str = trans_config_abspath(config_defaluts["model-directory"]),
                 use_defalut_parameter=False) -> None:
        """初始化模型"""

        # 未初始化但需要使用的属性
        self.result = None

        # 根目录
        if not os.path.isabs(root_dir):
            self.root_dir = os.path.abspath(root_dir)
        else:
            self.root_dir = root_dir
        #: :noindex:
        self.model_mode_dict = {1: os.path.join(root_dir, "fire.pt"),
                                2: os.path.join(root_dir, "people.pt"),
                                3: os.path.join(root_dir, "down.pt")}
        # 配置日志管理器
        self._create_logger()

        # 配置训练和预测的json文件路径
        self._train_config = Video_Detector.load_config(os.path.join(root_dir, "train_config.json"))
        self._predict_config = Video_Detector.load_config(os.path.join(root_dir, "predict_config.json"))
        # 默认路径优先级低于原优先级
        if not self._train_config:
            self._train_config = Video_Detector.load_config(defalut_train_config_path)
        if not self._predict_config:
            self._predict_config = Video_Detector.load_config(defalut_predict_config_path)

        # 是否加载默认参数
        # 否，则加载配置文件的内容
        if not use_defalut_parameter:
            batch, epochs, project, name, imgsz, data, weight_pt = self._train_config.values()
            model_mode, iou, conf, show, save_dir, max_frame = self._predict_config.values()
            device = self.get_device()
        # 是，则加载默认参数
        else:
            batch = 16
            epochs = 5
            project = 'train_file'
            name = 'detect'
            imgsz = 640
            data = 'fire.yaml'
            weight_pt = 'yolov8n.pt'
            model_mode = 1
            iou = 0.6
            conf = 0.5
            show = "True"
            save_dir = "detect_result"
            max_frame = 1800
            device = 0

        # 赋值给类成员变量
        self.batch = batch
        self.epochs = epochs
        if os.path.isabs(project):
            self.project = project
        else:
            self.project = os.path.join(root_dir, project)
        if os.path.isabs(name):
            self.name = name
        else:
            self.name = os.path.join(root_dir, name)
        self.imgsz = imgsz
        if os.path.isabs(project):
            self.data = data
        else:
            self.data = os.path.join(self.project, data)
        if os.path.isabs(weight_pt):
            self.weight_pt = weight_pt
        else:
            self.weight_pt = os.path.join(root_dir, weight_pt)

        self.train_model = YOLO(self.weight_pt)
        self.device = device

        # 可以在函数调用时被外界参数覆盖的变量
        self.model_mode = model_mode
        self.predict_model = {1: YOLO(self.model_mode_dict[1]), 2: YOLO(self.model_mode_dict[2]),
                              3: YOLO(self.model_mode_dict[3])}
        self.iou = iou
        self.conf = conf
        if show == "True":
            self.show = True
        else:
            self.show = False
        if os.path.isabs(save_dir):
            self.save_dir = save_dir
        else:
            self.save_dir = os.path.join(root_dir, save_dir)
        self.max_frame = max_frame

    def _create_logger(self):
        """创建日志处理器对象的实例，分别记录ERROR和INFO信息"""
        # 配置 error_logger 仅记录 ERROR 及以上级别的日志
        self.error_logger = Log_Processor(self.root_dir, 'error.log', Log_Processor.ERROR)
        # 配置 info_logger 记录所有级别的日志
        self.info_logger = Log_Processor(self.root_dir, 'info.log', Log_Processor.INFO)

    def reset_training_parameters(self, batch: int = None, epochs: int = None, project: str = None,
                                  name: str = None, imgsz: int = None, data: str = None,
                                  weight_pt: str = None, device: int = None):
        """
        重新设置模型训练时使用的参数，仅修改传入的参数，其他参数不变

        Parameters
        ----------
        batch: int
            每次训练时输入的图片数量，默认为16
        epochs: int
            训练迭代的次数，默认为5
        project: str
            训练文件存放的目录，默认在根目录下的train_file文件夹下
        name: str
            训练过程存放的文件，在project对应目录下创建子目录，存储训练的日志和输出结果
        imgsz: int
            输入图片的尺寸，默认要求640*640
        data: str
            有关数据集配置文件的路径，由于本项目目标主要是对火焰的识别，在yolov8下默认存放的是fire.yaml
            其默认路径为：ultralytics/cfg/datasets
            在该配置文件内按yolov8格式设置好训练集、验证集、测试集的图片路径，类别名等参数
        weight_pt: str
            预训练模型的文件名，可用于用户自行完成训练任务，当其不存在时yolov8会自动下载
        device: int
            可用设备的编号，此处主要用于设置CPU
        """

        # 赋值给实例变量
        if batch:
            self.batch = batch
        if epochs:
            self.epochs = epochs
        if project:
            if os.path.isabs(project):
                self.project = project
            else:
                self.project = os.path.join(self.root_dir, project)
        if name:
            if os.path.isabs(name):
                self.name = name
            else:
                self.name = os.path.join(self.root_dir, name)
        if imgsz:
            self.imgsz = imgsz
        if data:
            if os.path.isabs(data):
                self.data = data
            else:
                self.data = os.path.join(self.project, data)
        if weight_pt:
            if os.path.isabs(weight_pt):
                self.weight_pt = weight_pt
            else:
                self.weight_pt = os.path.join(self.root_dir, weight_pt)
            self.train_model = YOLO(weight_pt)
        # device可能是0
        if device is not None:
            self.device = device

    @staticmethod
    def load_config(path: str) -> dict:
        """
        读取配置文件
        Parameters
        ----------
        path: str
            传入json文件的相对路径
        Returns
        --------
        config_data: dict
            有关参数的字典
        """
        with open(path, 'r') as f:
            config_data = json.load(f)
        return config_data

    def get_device(self) -> Union[int, torch.device]:
        """
        确定进行识别的设备，需要判断GPU是否可用，不可用则使用CPU
        如果gpu可用则返回GPU的设备名并日志记录GPU信息，否则日志中记录CPU信息返回CPU字符串
        Returns
        --------
        device: Union[int, torch.device]
            GPU的设备编号或者CPU字符串
        """
        if torch.cuda.is_available():
            self.info_logger.log_write(f"Device is GPU: {torch.cuda.current_device()}",
                                       Log_Processor.INFO)
            # 获取当前默认 GPU 的索引
            return torch.cuda.current_device()
        self.info_logger.log_write("Device is CPU", Log_Processor.INFO)
        return torch.device('cpu')

    def set_default_model(self, mode: int):
        """
        设置默认使用模型
        Parameters
        ----------
        mode : int
            0设置使用全部模型，1设置使用火焰模型，2设置使用人像识别模型，3设置异常行为识别模型
        """
        self.model_mode = mode

    def train(self) -> None:
        """
        火焰识别模型的训练
        需要在类外设置好训练参数和配置文件，以及数据集
        """
        try:
            # begin train
            self.result = self.train_model.train(data=self.data, batch=self.batch,
                                                 epochs=self.epochs, imgsz=self.imgsz,
                                                 name=self.name, project=self.project,
                                                 device=self.device)
        except Exception as e:
            # catch all errors and export to the log
            error_type = type(e).__name__

            # self.error_logger.logger.error(你之前设置的部分)
            self.error_logger.logger.error(f"An error of type {error_type} occurred: {str(e)}",
                                            exc_info=True)

    def _one_model_predict(self, pre_source: Union[str, np.ndarray],
                           mode: int = None,
                           show: int = None,
                           iou: float = None,
                           conf: float = None) -> Optional[list[Results]]:
        """
        单个模型的预测函数，可以根据mode选择模型加载图片/视频进行预测，获得对应的返回结果
        是内置的方法，不提供对外接口，是predict函数的子部分

        Parameters
        ----------
        pre_source : Union[str, np.ndarray]
            用于推理的的特定数据源，可以是矩阵，图片路径，URL，视频路径或者设备id
            支持广泛的格式和来源，实现了跨不同类型输入的灵活应用。
        mode : int
            指定使用的识别模型，未指定(为None)时使用内部的默认模式对应的模型进行识别
        show: bool
            指定模型的预测结果是否可视化，未指定(为None)时使用默认值
        iou: float
            指定衡量预测边界框与真实边界框之间重叠程度，未指定(为None)时使用默认值
        conf: float
            指定模型对识别设置的置信度阈值，未指定(为None)时使用默认值

        Returns
        -------
        result_list : Optional[list[Results]]
            yolov8内置的结果对象序列，每个元素为一个Result对象，其中包括了识别结果的各项信息
        """
        # 根据传入参数进行调整
        if mode == 0:
            return None
        elif mode is None and self.model_mode == 0:
            return None
        elif mode is None and self.model_mode != 0:
            mode = self.model_mode

        if show is None:
            show = self.show
        if iou is None:
            iou = self.iou
        if conf is None:
            conf = self.conf
        # 根据不同模式，进行不同模型的预测
        try:
            if isinstance(pre_source, str):
                if mode == 2:
                    result = self.predict_model[mode].predict(
                        stream=True,
                        show=show,
                        source=pre_source,
                        iou=iou,
                        conf=conf,
                        device=self.device,
                        classes=0)
                else:
                    result = self.predict_model[mode].predict(
                        stream=True,
                        show=show,
                        source=pre_source,
                        iou=iou,
                        conf=conf,
                        device=self.device)
            else:
                if mode == 2:
                    result = self.predict_model[mode].predict(
                        stream=False,
                        show=show,
                        source=pre_source,
                        iou=iou,
                        conf=conf,
                        device=self.device,
                        classes=0)
                else:
                    result = self.predict_model[mode].predict(
                        stream=False,
                        show=show,
                        source=pre_source,
                        iou=iou,
                        conf=conf,
                        device=self.device)
            return list(result)

        except Exception as e:
            # 将捕获的错误存储到日志中
            error_type = type(e).__name__
            self.error_logger.logger.error("An error of type %s occurred: %s", error_type, str(e),
                                           exc_info=True)

    def predict(self, pre_source: Union[str, np.ndarray],
                mode: int = None,
                show: int = None,
                iou: float = None,
                conf: float = None) -> Optional[dict[int, list[Results]]]:
        """
        模型预测函数，可以根据mode选择模型加载图片/视频进行预测，获得对应的返回结果
        允许mode为0，此时会调用所有模型进行识别，保存得到三个结果对象序列，使用字典将其与对应的模式进行映射

        Parameters
        ----------
        pre_source : Union[str, np.ndarray]
            用于推理的的特定数据源，可以是矩阵，图片路径，URL，视频路径或者设备id
            支持广泛的格式和来源，实现了跨不同类型输入的灵活应用。
        mode : int
            指定使用的识别模型，未指定(为None)时使用内部的默认模式对应的模型进行识别
        show: bool
            指定模型的预测结果是否可视化，未指定(为None)时使用默认值
        iou: float
            指定衡量预测边界框与真实边界框之间重叠程度，未指定(为None)时使用默认值
        conf: float
            指定模型对识别设置的置信度阈值，未指定(为None)时使用默认值

        Returns
        -------
        result_dict : Optional[dict[int, list[Results]]]
            由模式-yolov8内置的结果对象序列组成你的字典，每个元素为一个模型-Result对象序列的键值对
            通过访问对应模式对应的值，可以获得识别结果的各项信息
        """
        result = {}
        if mode == 0:
            result[1] = self._one_model_predict(pre_source, 1, show, iou, conf)
            result[2] = self._one_model_predict(pre_source, 2, show, iou, conf)
            result[3] = self._one_model_predict(pre_source, 3, show, iou, conf)
        elif mode == 1:
            result[1] = self._one_model_predict(pre_source, 1, show, iou, conf)
        elif mode == 2:
            result[2] = self._one_model_predict(pre_source, 2, show, iou, conf)
        elif mode == 3:
            result[3] = self._one_model_predict(pre_source, 3, show, iou, conf)
        else:
            return None
        return result

    def model_plot(self, frame: np.ndarray, results1: Results = None,
                   results2: Results = None, results3: Results = None) -> np.ndarray:
        """
        识别碰撞箱绘制函数，使用全部模型检测时，需要根据各模型结果对原始图像进行各自的碰撞箱绘制
        Parameters
        ----------
        frame : np.ndarray
            传入的原始图像
        results1 : Results
            火焰识别模型的识别结果，如果为None，则不绘制
        results2 : Results
            人像识别模型的识别结果，如果为None，则不绘制
        results3
            异常行为识别模型的识别结果，如果为None，则不绘制
        Returns
        -------
        frame : np.ndarray
            绘制各碰撞箱后的结果图像
        """

        # 在图像上绘制边界框
        if results1 is not None:
            for box in results1.boxes:
                # 获取边界框坐标
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                # 获取置信度和标签
                confidence = box.conf[0]
                label = box.cls[0]
                # 绘制矩形边界框
                cv.rectangle(frame, (x1, y1), (x2, y2),
                             self.predict_class_type_color_dict[1][int(label)], 2)
                # 在边界框上绘制标签和置信度
                label_text = f'{self.predict_model[1].names[int(label)]}: {confidence:.2f}'
                cv.putText(frame, label_text, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.6,
                           (255, 255, 255), 2)
        # 其他同理
        if results2 is not None:
            for box in results2.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0]
                label = box.cls[0]
                cv.rectangle(frame, (x1, y1), (x2, y2),
                             self.predict_class_type_color_dict[2], 2)
                label_text = f'{self.predict_model[2].names[int(label)]}: {confidence:.2f}'
                cv.putText(frame, label_text, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.6,
                           (255, 255, 255), 2)
        if results3 is not None:
            for box in results3.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0]
                label = box.cls[0]
                cv.rectangle(frame, (x1, y1), (x2, y2),
                             self.predict_class_type_color_dict[3], 2)
                label_text = f'{self.predict_model[3].names[int(label)]}: {confidence:.2f}'
                cv.putText(frame, label_text, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.6,
                           (255, 255, 255), 2)
        return frame

    def detect(self, frame_queue: multiprocessing.Queue,
               result_queue: multiprocessing.Queue,
               mode: int = None,
               save_dir: str = None, max_frame: int = None,
               iou: float = None, sensitivity: int = 0) -> None:
        """
        对摄像头捕捉视频帧的实时检测和处理函数，是视频检测器的核心处理函数
        通过多进程的视频帧队列从视频流处理器对象处获得视频帧
        并通过另一个队列将检测后的错误码和每个预测类型的对应置信度返回给视频流处理器对象，完成进程通信
        Parameters
        ----------
        frame_queue : multiprocessing.Queue
            视频流对象传入的视频帧队列，用于获得要处理的视频帧队列
        result_queue : multiprocessing.Queue
            返回给视频流对象的处理队列，用于返回错误码和置信度
        mode : int
            指定的模式，用户指定后由视频流处理器传给当前的检测器实例，以完成用户要求的检测功能
        save_dir : str
            指定的视频保存路径，目前不提供设置方式，需要在进一步优化后完成设置
        max_frame : int
            指定的最大缓冲区帧数，因为无法直接解析视频设备的帧率，故暂未用于实践
        iou : float
            指定衡量预测边界框与真实边界框之间重叠程度，未指定(为None)时使用默认值
        sensitivity : int
            指定对异常的敏感程度，0对应低敏感程度，设置置信度阈值为0.6，1对应高敏感程度，设置置信度阈值为0.5，默认为低敏感

        Notes
        -----
        传入的视频帧使用具有限定大小的双端队列进行处理
        每次从传入视频帧队列中获得全部视频帧按先入先出的顺序进行存储，随后从队列末尾取最实时的视频帧进行检测
        这相对于对双端队列中未取出检测的视频帧进行了识别丢帧处理，但能够被保存
        最终处理的视频帧比例由设备性能和进程被分配的资源决定
        既能保存异常出现的前因后果，又可以保证处理的实时性
        """

        # 设置mode和save_dir，max_frame
        # iou和conf在self.predict里设置
        if mode is None:
            mode = self.model_mode
        if save_dir is None:
            save_now = datetime.datetime.now().strftime(Log_Processor.strftime_all)
            save_dir = os.path.join(self.save_dir, save_now)
            self.make_dir(save_dir)
        if not os.path.isabs(save_dir):
            save_dir = os.path.join(self.root_dir, save_dir)
            self.make_dir(save_dir)
        if max_frame is None:
            max_frame = self.max_frame
        if sensitivity == 0:
            conf = 0.6
        else:
            conf = 0.5
        # 进程调用需要重新创建一些对象
        self._create_logger()
        self.info_logger.log_write("Video Detector start detect", Log_Processor.INFO)
        # 缓冲区，保存限定数量的视频帧
        save_frame_deque = deque(maxlen=max_frame)
        # 写入有问题部分及前后的视频流到文件的对象
        warning_video_out = None

        # 读取视频帧队列是否为空
        flag_wait = False
        # 错误视频帧标记和等待传入视频帧时间记录
        warning_flag = False
        # 已传输过的错误类型的记录
        warning_type_record = 0
        # 已传输过的错误类型的最大置信度的记录
        warning_conf_record = [0, 0, 0, 0]
        # 最后一次识别到错误的视频帧之后的无无措视频帧数量
        no_warning_frame = 0
        # 运行的开始时间
        start_wait_time = time.time()
        # 主循环
        while True:
            try:
                # 判断另一进程是否结束
                if frame_queue.empty():
                    # 未处于等待状态，说明之前处理了视频帧，从此处开始等待
                    if not flag_wait:
                        flag_wait = True
                        # 记录开始等待时间
                        start_wait_time = time.time()
                        continue
                    # 处理等待状态
                    else:
                        # 如果等待的时间超过了15s，结束运行
                        if time.time() - start_wait_time >= 15:
                            self.error_logger.log_write(f"Timed out waiting for video frame." +
                                                        f" Video Detector stop waiting " +
                                                        f"and exit the detect process",
                                                        Log_Processor.ERROR)
                            break
                        # 否则继续循环
                        else:
                            continue

                # 如果不为空，重置等待状态，重计时
                else:
                    flag_wait = False
                    start_wait_time = time.time()

                # 保存当前传入的全部帧
                for _ in range(frame_queue.qsize()):
                    save_frame_deque.append(frame_queue.get())
                # 弹出最新帧，使其能够处理最新帧
                frame = save_frame_deque.pop()

                # 传入结束标志，需要清空result_queue再关闭，并释放warning_video_out
                if frame is None:
                    for _ in range(result_queue.qsize()):
                        result_queue.get()
                    self.info_logger.log_write(f"Detect finish. Please cheack the {save_dir}",
                                               Log_Processor.INFO)
                    if warning_video_out is not None:
                        warning_video_out.release()
                    return

                # 否则处理最新帧
                else:
                    # 预测视频帧获得结果
                    predict_result = self.predict(pre_source=frame, mode=mode,
                                                  show=False, iou=iou, conf=conf)
                    # 记录错误码
                    warning_mode = 0
                    # 记录每类错误的最大置信度
                    warning_conf = [0, 0, 0, 0]
                    # 全部识别模式和单个模型模式的出现错误的范围不同
                    if mode == 0:
                        # 遍历三个模型的预测结果
                        for i in range(1, 4):
                            # 遍历预测图片的碰撞箱
                            for box in predict_result[i][0].boxes:
                                for box_error in set(box.cls.tolist()):
                                # 获得错误码和每个错误类型的最大置信度
                                    warning_mode |= self.mode_precdict_warning_mode[i][box_error]
                                    warning_conf[self.mode_precdict_class[i][box_error]] = \
                                        max(warning_conf[self.mode_precdict_class[i][box_error]],
                                            max(box.conf.tolist()))
                    else:
                        # 遍历使用模型的预测结果，获得错误码和错误类型的最大置信度
                        for box in predict_result[mode][0].boxes:
                            for box_error in set(box.cls.tolist()):
                                # 获得错误码和每个错误类型的最大置信度
                                warning_mode |= self.mode_precdict_warning_mode[mode][box_error]
                                warning_conf[self.mode_precdict_class[mode][box_error]] = \
                                    max(warning_conf[self.mode_precdict_class[mode][box_error]],
                                        max(box.conf.tolist()))

                    # 出现错误时
                    if warning_mode:
                        # 全部识别模式保存检测框内图像并需要重新绘制图像
                        if mode == 0:
                            predict_frame = self.model_plot(predict_result[1][0].orig_img,
                                                            predict_result[1][0], predict_result[2][0],
                                                            predict_result[3][0])
                        # 单个模型识别模式保存检测框内图像并绘制图像
                        else:
                            predict_frame = predict_result[mode][0].plot()
                        # 将预测帧结果放回缓冲队列
                        save_frame_deque.append(predict_frame)
                        # 如果不在警告标志范围内
                        if not warning_flag:
                            # 发送警告信息，包括错误码和置信度的二元素列表
                            result_queue.put([warning_mode, warning_conf])
                            # 记录已发送的错误类型和最大置信度
                            warning_type_record |= warning_mode
                            warning_conf_record = warning_conf
                            warning_flag = True
                            # 利用VideoWriter保存有问题部分及前后的视频流，
                            # 文件路径为生成路径，帧率和分辨率统一为限制后的视频大小和帧率，彩色模式
                            fourcc = cv.VideoWriter.fourcc(*"DIVX")
                            save_name = datetime.datetime.now().strftime(Log_Processor.strftime_all)
                            warning_video_path = os.path.join(save_dir, f"{save_name}.avi")
                            warning_video_out = cv.VideoWriter(warning_video_path, fourcc, 30,
                                                               (predict_frame.shape[1],
                                                                predict_frame.shape[0]), True)
                            # 将缓冲区的全部视频帧写入
                            while save_frame_deque:
                                warning_video_out.write(save_frame_deque.popleft())
                            # 日志记录
                            self.error_logger.log_write("Video Detector Warning!!!\n"
                                                        f"The warning code is {warning_mode}, "
                                                        f"the warning conf is {warning_conf}",
                                                        Log_Processor.ERROR)

                        # 如果在警告标志范围内
                        else:
                            new_warning_code = 0
                            # 比较新的错误的最大置信度等级是否比原最大置信度等级高
                            for i in range(len(warning_conf_record)):
                                # 如果是，此位置需要发送新的错误信息，并记录该最大置信度
                                # 未发送过的错误类型在判断中也被保存了
                                if Warning_Processor.get_level_description(warning_conf_record[i], sensitivity) < \
                                   Warning_Processor.get_level_description(warning_conf[i], sensitivity):
                                    new_warning_code |= self.warning_mode_list[i]
                                    warning_conf_record[i] = warning_conf[i]
                            # 如果有需要发送新的错误信息，则发送对应的警告信息
                            if new_warning_code:
                                result_queue.put([new_warning_code, warning_conf])
                                warning_type_record |= new_warning_code
                                # 日志记录
                                self.error_logger.log_write("Video Detector Warning!!!\n"
                                                            f"The warning code is {warning_mode}, "
                                                            f"the warning conf is {warning_conf}",
                                                            Log_Processor.ERROR)

                            # 将缓冲区的全部视频帧写入
                            while save_frame_deque:
                                warning_video_out.write(save_frame_deque.popleft())
                        # 重新记录无问题视频帧数量
                        no_warning_frame = 0

                    # 无错误时
                    else:
                        # 正常返回原视频帧
                        save_frame_deque.append(frame)
                        # 检测前面出现问题时，当前是否经过了max_frame帧
                        if warning_flag:
                            # 先将缓冲区的全部视频帧写入
                            if warning_video_out is not None:
                                while save_frame_deque:
                                    warning_video_out.write(save_frame_deque.popleft())
                            # 如果经过了max_frame帧
                            no_warning_frame += 1
                            if no_warning_frame == max_frame:
                                # 重置警告标志
                                warning_flag = False
                                # 释放写视频文件对象
                                warning_video_out.release()
                                # 重置无发送错误类型
                                warning_type_record = 0

            # 错误处理
            except Exception as e:
                # catch all errors and export to the log
                error_type = type(e).__name__
                self.error_logger.logger.error("An error of type %s occurred: %s", error_type, str(e),
                                               exc_info=True)
                break

    def re_detect(self, video_file: str, ui_event=None,
                  mode: int = None,
                  save_dir: str = None, max_frame: int = None,
                  iou: float = None, sensitivity: int = 0) -> None:
        """
        对传入视频路径的视频的检测和处理函数，是视频检测器的另一个核心处理函数
        被创建后作为独立的进程运行，不受视频处理器的创建进程影响，只受ui界面的停止命令影响
        Parameters
        ----------
        video_file : str
            要处理视频的指定绝对路径
        ui_event : multiprocessing.Event
            用于监听ui界面的停止信息的事件
        mode : int
            指定的模式，用户指定后由视频流处理器传给当前的检测器实例，以完成用户要求的检测功能
        save_dir : str
            指定的视频保存路径，目前不提供设置方式，需要在进一步优化后完成设置
        max_frame : int
            指定的最大缓冲区帧数，因为无法直接解析视频设备的帧率，故暂未用于实践
        iou : float
            指定衡量预测边界框与真实边界框之间重叠程度，未指定(为None)时使用默认值
        sensitivity : int
            指定对异常的敏感程度，0对应低敏感程度，设置置信度阈值为0.6，1对应高敏感程度，设置置信度阈值为0.5，默认为低敏感
        """

        # 设置mode和save_dir，max_frame
        # iou和conf在self.predict里设置
        if mode is None:
            mode = self.model_mode
        if save_dir is None:
            save_dir = self.save_dir
        elif not os.path.isabs(save_dir):
            save_dir = os.path.join(self.root_dir, save_dir)
        if max_frame is None:
            max_frame = self.max_frame
        # 如果是低敏感度，置信度conf默认为0.6
        if sensitivity == 0:
            conf = 0.6
        # 如果是高敏感度，置信度conf默认为0.5（更容易被监测到）
        else:
            conf = 0.5

        # 进程调用需要重新创建一些对象
        self._create_logger()
        self.info_logger.log_write("Video Detector start re-detect", Log_Processor.INFO)

        # 对整个视频流进行完整的预测处理
        predict_result = self.predict(pre_source=video_file, mode=mode,
                                      show=False, iou=iou, conf=conf)

        # 预测完成后才能退出，如果要求退出则退出
        if ui_event is not None:
            if ui_event.is_set():
                return

        # 获得当前时间
        now = datetime.datetime.now().strftime(Log_Processor.strftime_all)
        # 根据save_dir和当前时间记录要使用的绝对路径
        use_dir = os.path.join(save_dir, "re-detect_"+now)
        # 创建目录来保存识别结果(包括了子路径video的创建)
        self.make_dir(os.path.join(use_dir, "video"))

        # 日志记录
        self.info_logger.log_write("Finish re-detect. Start saving...\n"
                                   f"The save dir is {use_dir}.", Log_Processor.INFO)

        # 用队列存储处理结果帧，缓冲区限制大小
        frame_queue = deque(maxlen=max_frame)
        # 视频帧索引
        frame_index = 0
        # 错误标记
        flag_error = False
        warning_video_out = None
        # 全部类型识别
        if mode == 0:
            # 遍历三个模型对每个视频帧的处理结果
            for result in zip(predict_result[1], predict_result[2], predict_result[3]):
                # 如果要求退出则退出
                if ui_event is not None:
                    if ui_event.is_set():
                        return
                # 如果这三个result中出现了任意一个检测类型
                if len(result[0].boxes.cls) != 0 or \
                   len(result[1].boxes.cls) != 0 or \
                   len(result[2].boxes.cls) != 0:
                    # 用model_plot绘制加入碰撞箱之后的原始视频帧
                    frame = self.model_plot(result[0].orig_img, result[0], result[1], result[2])
                    # 将问题帧用图片保存起来
                    save_path = os.path.join(use_dir, f"frame_{frame_index}.jpg")
                    cv.imwrite(save_path, frame)
                    # 将问题帧加入队列
                    frame_queue.append(frame)
                    if not flag_error:
                        flag_error = True
                        # 创建视频写入流，利用VideoWriter保存有问题部分及前后的视频流，
                        # 文件路径为生成路径，帧率和分辨率统一为限制后的视频大小和帧率，彩色模式
                        fourcc = cv.VideoWriter.fourcc(*"DIVX")
                        warning_video_path = os.path.join(use_dir, "video", "1_re-detect.avi")
                        warning_video_out = cv.VideoWriter(warning_video_path, fourcc, 30,
                                                           (frame.shape[1],
                                                            frame.shape[0]), True)
                        if warning_video_out.isOpened():
                            self.info_logger.log_write("Start video save", Log_Processor.INFO)

                    if warning_video_out is not None:
                        # 将缓冲区的全部视频帧写入
                        while frame_queue:
                            warning_video_out.write(frame_queue.popleft())
                # 否则只保存视频帧即可
                else:
                    frame_queue.append(result[0].orig_img)
                frame_index += 1

        # 如果只选择单个的模型
        else:
            for result in predict_result[mode]:
                # 如果要求退出则退出
                if ui_event is not None:
                    if ui_event.is_set():
                        return
                # results是一个Results对象
                boxes = result.boxes
                frame = result.plot()
                frame_queue.append(frame)
                # 如果监测到了类型，进行图片保存
                if len(boxes.cls) != 0:
                    result.save(filename=os.path.join(use_dir, f"frame_{frame_index}.jpg"))
                    if not flag_error:
                        flag_error = True
                        # 创建视频写入流，利用VideoWriter保存有问题部分及前后的视频流，
                        # 文件路径为生成路径，帧率和分辨率统一为限制后的视频大小和帧率，彩色模式
                        fourcc = cv.VideoWriter.fourcc(*"DIVX")
                        warning_video_path = os.path.join(use_dir, "video", "1_re-detect.avi")
                        warning_video_out = cv.VideoWriter(warning_video_path, fourcc, 30,
                                                           (frame.shape[1],
                                                            frame.shape[0]), True)

                        if warning_video_out.isOpened():
                            self.info_logger.log_write("Start video save", Log_Processor.INFO)
                    if warning_video_out is not None:
                        # 将缓冲区的全部视频帧写入
                        while frame_queue:
                            warning_video_out.write(frame_queue.popleft())
                frame_index += 1

        # 日志记录
        self.info_logger.log_write("Save finish", Log_Processor.INFO)
        if warning_video_out is not None:
            warning_video_out.release()

    def make_dir(self, dir_path: str):
        """
        创建空目录函数，需要写入日志处理器，不是静态方法
        此处不会检测上一级是否有目录，而是按照目录直接逐级创建
        Parameters
        ----------
        dir_path : str
            指定的要创建的目录的绝对路径
        """
        caller_info: str = 'make_dir'
        try:
            # 如果目录不存在，则创建目录
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                self.info_logger.logger.info(f"[{caller_info}] Directory '{dir_path}' created successfully.")
            else:
                self.info_logger.logger.info(f"Directory '{dir_path}' already exists.")
        except Exception as e:
            # catch all errors and export to the log
            error_type = type(e).__name__
            self.error_logger.logger.error("An error of type %s occurred: %s", error_type, str(e),
                                           exc_info=True)

    def delete_dir(self, directory: str):
        """
        删除目录函数，需要写入日志处理器，不再是静态方法
        被删除的目录下不允许有子目录
        Parameters
        ----------
        directory : str
            指定的要删除的目录的绝对路径
        Returns
        -------
        """
        try:
            # 遍历目录中的所有文件
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                # 如果是文件则删除
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    self.info_logger.logger.info(f"File '{file_path}' removed successfully.")
            self.info_logger.logger.info(f"All files in directory '{directory}' cleared successfully.")
        except Exception as e:
            self.error_logger.logger.error(f"Failed to clear files in directory '{directory}'. Error: {e}")

    def show_csv(self):
        """
        对训练完成后的各种评估参数绘制图像
        """
        try:
            IPython.get_ipython().run_line_magic('matplotlib', 'inline')
            header = []
            with open(self.project + self.name + 'results.csv', 'r') as f:
                result_csv = csv.reader(f)  # 读取csv文件
                data = list(result_csv)  # csv数据转换为列表
                result = {}
                # 获取x轴的标签
                header = data[0]
                for row in header:
                    result[row] = []
                # 对csv每列作为字典 字典的键是x轴标签 值对应的是各个评估参数的列表
                for i, row in enumerate(data):
                    if i == 0:
                        continue
                    for index, j in enumerate(row):
                        result[header[index]].append(j)
                x = result[header[0]]
                for index, i in enumerate(x):
                    x[index] = int(i)
                for index, val in enumerate(result.values()):
                    if index == 0:
                        continue
                    for ind, y in enumerate(val):
                        val[ind] = float(y)
                    plt.figure(figsize=(2, 2))
                    plt.xlabel(header[0], )
                    plt.ylabel(header[index], rotation='horizontal')
                    plt.plot(x, val)
                    plt.show()
        except Exception as e:
            # catch all errors and export to the log
            error_type = type(e).__name__
            logging.error("An error of type %s occurred: %s", error_type, str(e))
            logging.error("Detailed traceback information:", exc_info=True)


if __name__ == '__main__':
    # 初始化类实例
    video_detector = Video_Detector()

    # 查看存储的变量是否和配置文件一致
    for i in video_detector.__dict__.items():
        print(i)

    # 调用类方法选择模型
    video_detector.set_default_model(1)

    # 使用各个模型进行视频识别预测
    source = os.path.abspath("../../Model/test/fire.mp4")
    Results_list = video_detector.predict(pre_source=source, mode=1)
    # 输出错误结果
    for i in Results_list[1]:
        print(i.boxes.cls.tolist())
        print(i.boxes.conf.tolist())

    video_detector.re_detect(video_file=source, mode=1, sensitivity=0)
