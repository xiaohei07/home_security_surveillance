# -*- coding: utf-8 -*-
"""
File Name: video_detect.py
Author: youyou
Date: 2024-05-02
Version: 1.0
Description: 使用yolov8，对视频帧进行识别，判断监控是否出现了火灾/人/异常行为
"""
import os.path

# 引入常用库
from home_security_surveillance.common import *
# 用日志处理器
from home_security_surveillance.file_process.log import *
# 用config模块获得默认目录位置
from home_security_surveillance.file_process.config import config_defaluts, trans_config_abspath
# 用torch
import torch
# 用yolo类
from ultralytics import YOLO
# 用Results类
from ultralytics.engine.results import Results

# 用plt绘出csv结果图
import csv
import matplotlib.pyplot as plt
# 双端队列做缓冲
from collections import deque
import IPython

__all__ = ["Video_Detector"]

### 训练和预测配置文件的默认路径
defalut_train_config_path = os.path.normpath(
    os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(__file__))), "./Model/train_config.json"))

defalut_predict_config_path = os.path.normpath(
    os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(__file__))), "./Model/predict_config.json"))


class Video_Detector(object):
    """
    Represent application of the Yolov8 flame recognition model
    
    Attributes:
        model_mode_dict(dict):有关模型的字典 1：火焰模型 2：人物模型 3：火焰和人物模型

        batch(int)每次训练时输入的图片数量:The number of images entered in one training session
        
        epochs(int)训练迭代的次数:Number of rounds trained
        
        project(str)训练文件存放的目录:The directory where the training files are stored
        
        name(str)训练过程存放的文件:Name of the training run.
                                Used for creating a subdirectory within the project folder,
                                where training logs and outputs are stored.
                                For example: './project/name'
        
        imgsz(int)输入图片的大小:Enter the size of the image
        
        data(str)有关数据集配置文件的路径:The path where the configuration file is located
        the default path is in the 'ultralytics/cfg/datasets'
        
        weight_pt(str)预训练模型-文件名:The path of the pretrained model
    """

    # 获取相关参数(可以让用户选择模式) 前端通过修改predict_config.json中的model_mode来改变模式
    # 配置文件的参数都可以和用户进行交互

    # 类型说明
    predict_class_type_num = [0, 1]
    predict_class_type_color_dict = {0: (0, 0, 255), 1: (128, 128, 128),
                                     2: (0, 255, 0), 3: (255, 0, 0)}

    ### 新增参数root_dir，默认目录用下面的方法获得
    def __init__(self, root_dir: str = trans_config_abspath(config_defaluts["model-directory"]),
                 use_defalut_parameter=False) -> None:

        """
        初始化模型
        Initializes an instance of the yolov8_model class.
        
        Args:
            root_dir(str): The root directory of Video_Detector class use
        """
        # 未初始化但需要使用的属性
        self.result = None

        ###  新增部分
        # 根目录
        if not os.path.isabs(root_dir):
            self.root_dir = os.path.abspath(root_dir)
        else:
            self.root_dir = root_dir
        # model_mode_dict将相对路径改为绝对路径，路径根目录用root_dir
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
            project = 'runs'
            name = 'detect'
            imgsz = 640
            data = 'default.yaml'
            weight_pt = 'yolov8n.pt'
            device = 0
            max_frame = 900
            iou = 0.6
            conf = 0.8
            show = "True"
            save_dir = "test"
            model_mode = 1

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
        # 配置 error_logger 仅记录 ERROR 及以上级别的日志
        self.error_logger = Log_Processor(self.root_dir, 'error.log', Log_Processor.ERROR)
        # 配置 info_logger 记录所有级别的日志
        self.info_logger = Log_Processor(self.root_dir, 'info.log', Log_Processor.INFO)

    ###  新增方法，重设训练参数
    def reset_training_parameters(self, batch: int = 16, epochs: int = 5, project: str = 'runs',
                                  name: str = 'detect', imgsz: int = 640, data: str = 'default.yaml',
                                  weight_pt: str = 'yolov8n.pt', device=0):
        """
        重新设置模型训练时使用的参数
        Args:
            batch(int):The number of images entered in one training session

            epochs(int):Number of rounds trained

            project(str):The directory where the training files are stored

            name(str):Name of the training run.
                      Used for creating a subdirectory within the project folder,
                      where training logs and outputs are stored.
                      For example: './project/name'

            imgsz(int):Enter the size of the image

            data(str):The path where the configuration file is located
            the default path is in the 'ultralytics/cfg/datasets'

            weight_pt(str):The path of the pretrained model

            device(int): 可用设备的编号
        """

        # 赋值给类成员变量
        self.batch = batch
        self.epochs = epochs
        if os.path.isabs(project):
            self.project = project
        else:
            self.project = os.path.join(self.root_dir, project)
        if os.path.isabs(name):
            self.name = name
        else:
            self.name = os.path.join(self.root_dir, name)
        self.imgsz = imgsz
        if os.path.isabs(project):
            self.data = data
        else:
            self.data = os.path.join(self.project, data)
        if os.path.isabs(weight_pt):
            self.weight_pt = weight_pt
        else:
            self.weight_pt = os.path.join(self.root_dir, weight_pt)
        self.train_model = YOLO(weight_pt)
        self.device = device

    ###  新增方法
    @staticmethod
    def load_config(path: str) -> dict:
        """
        作用：
            读取配置文件

        参数：
            path(str):传入json文件的相对路径

        返回:
            config_data(dict):有关参数的字典
        """
        with open(path, 'r') as f:
            config_data = json.load(f)
        return config_data

    ### 新增方法，修改了日志处理器部分
    def get_device(self):
        """
        作用：
            判断gpu是否可用

        参数：
            无

        返回：
            如果gpu可用则返回gpu的设备并打印gpu信息，否则打印cpu信息
        """
        if torch.cuda.is_available():
            self.info_logger.log_write(f"Device is GPU: {torch.cuda.current_device()}",
                                       Log_Processor.INFO)
            # 获取当前默认 GPU 的索引
            return torch.cuda.current_device()
        self.info_logger.log_write("Device is CPU", Log_Processor.INFO)
        return torch.device('cpu')

    ### 修改默认模式的，修改后永久改变使用识别模型
    def select_default_model(self, mode: int):
        """
        作用：
            根据用户的选择去挑选不同的模型

        参数：
            eg:model_mode.keys():1 2 3
               model_mode.values(): "fire.pt" "people.pt" "all.pt"
        返回：
            对应模型的相对路径
        """
        self.model_mode = mode

    def train(self) -> None:
        """
        Start training the flame recognition model
        
        Returns:
            a list of Results objects
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

            ### 修改日志处理器部分,也可以这样写，因为我写的这个部分是追踪不到堆栈的
            # self.error_logger.logger.error(你之前设置的部分)
            self.error_logger.logger.error(f"An error of type {error_type} occurred: {str(e)}",
                                            exc_info=True)

    def _one_model_predict(self, pre_source: Union[str, np.ndarray],
                           mode: int = None,
                           show: int = None,
                           iou: float = None,
                           conf: float = None) -> Optional[list[Results]]:

        """
        作用：
            用训练好的模型进行预测
        
        参数:
            source(Union[str, np.ndarray]):需要预测的数据源
            Specifies the data source for inference.
            Can be an image path, video file, directory, URL, or device ID for live feeds.
            Supports a wide range of formats and sources, enabling flexible application across different types of input.
            
            iou(float):非最大抑制 （NMS） 的交集并集 （IoU） 阈值。值越低，通过消除重叠框来减少检测次数，这对于减少重复项很有用。
            Intersection Over Union (IoU) threshold for Non-Maximum Suppression (NMS).
            Lower values result in fewer detections by eliminating overlapping boxes, useful for reducing duplicates.

            conf(float):设置检测的最低置信度阈值。低于此阈值的置信度检测到的对象将被忽略。调整此值有助于减少误报。
        """
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
        try:
            # begin predict
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
                        stream=True,
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
            # catch all errors and export to the log
            ### 修改日志记录器的形式，和上面的修改不同，想不变的话可以这么写:
            error_type = type(e).__name__
            self.error_logger.logger.error("An error of type %s occurred: %s", error_type, str(e),
                                           exc_info=True)

    def predict(self, pre_source: Union[str, np.ndarray],
                mode: int = None,
                show: int = None,
                iou: float = None,
                conf: float = None) -> Optional[dict[int, list[Results]]]:
        result = {}
        if mode == 0:
            result[1] = self._one_model_predict(pre_source, 1, show, iou, conf)
            result[2] = self._one_model_predict(pre_source, 2, show, iou, conf)
            result[3] = self._one_model_predict(pre_source, 2, show, iou, conf)
        elif mode == 1:
            result[1] = self._one_model_predict(pre_source, 1, show, iou, conf)
        elif mode == 2:
            result[2] = self._one_model_predict(pre_source, 2, show, iou, conf)
        elif mode == 3:
            result[3] = self._one_model_predict(pre_source, 3, show, iou, conf)
        else:
            return None
        return result

    def three_model_plot(self, frame: np.ndarray,
                        results1: Results, results2: Results, results3: Results):

        # 在图像上绘制边界框
        for box in results1.boxes:
            # 获取边界框坐标
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            # 获取置信度和标签
            confidence = box.conf[0]
            label = box.cls[0]
            # 绘制矩形边界框
            cv.rectangle(frame, (x1, y1), (x2, y2),
                         self.predict_class_type_color_dict[int(label)], 2)
            # 在边界框上绘制标签和置信度
            label_text = f'{self.predict_model[1].names[int(label)]}: {confidence:.2f}'
            cv.putText(frame, label_text, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5,
                       (255, 255, 255), 2)

        for box in results2.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = box.conf[0]
            label = box.cls[0]
            cv.rectangle(frame, (x1, y1), (x2, y2),
                         self.predict_class_type_color_dict[2], 2)
            label_text = f'{self.predict_model[2].names[int(label)]}: {confidence:.2f}'
            cv.putText(frame, label_text, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5,
                       (255, 255, 255), 2)
        for box in results3.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = box.conf[0]
            label = box.cls[0]
            cv.rectangle(frame, (x1, y1), (x2, y2),
                         self.predict_class_type_color_dict[3], 2)
            label_text = f'{self.predict_model[2].names[int(label)]}: {confidence:.2f}'
            cv.putText(frame, label_text, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5,
                       (255, 255, 255), 2)
            return frame

    def detect(self, frame_queue: multiprocessing.Queue,
               result_queue: multiprocessing.Queue,
               mode: int = None,
               save_dir: str = None, max_frame: int = None,
               iou: float = None, conf: float = None) -> None:

        # 设置mode和save_dir，max_frame
        # iou和conf在self.predict里设置
        if mode is None:
            mode = self.model_mode
        if save_dir is None:
            save_dir = self.save_dir
        if not os.path.isabs(save_dir):
            save_dir = os.path.join(self.root_dir, save_dir)
        if max_frame is None:
            max_frame = self.max_frame

        # 缓冲区，保存限定长度的视频帧
        save_frame_deque = deque(maxlen=max_frame)
        warning_video_out = None
        # 错误视频帧标记和等待传入视频帧时间记录
        warning_flag = False
        no_warning_frame = 0
        flag_wait = False
        start_wait_time = time.time()
        self._create_logger()
        self.info_logger.log_write("Video Detector start detect", Log_Processor.INFO)
        while True:
            try:
                # 判断另一进程是否结束
                if frame_queue.empty():
                    if not flag_wait:
                        flag_wait = True
                        start_wait_time = time.time()
                        continue
                    else:
                        if time.time() - start_wait_time >= 5:
                            self.error_logger.log_write(f"Timed out waiting for video frame." +
                                                        f" Video Detector stop waiting " +
                                                        f"and exit the detect process",
                                                        Log_Processor.ERROR)
                            break
                        else:
                            continue
                else:
                    flag_wait = False
                    start_wait_time = time.time()

                # 对传进来的帧进行处理
                frame = frame_queue.get()
                # 传入结束标志，需要清空result_queue再关闭，并释放warning_video_out
                if frame is None:
                    for i in range(result_queue.qsize()):
                        print(result_queue.get())
                    self.info_logger.log_write(f"Detect finish. Please cheack the {save_dir}",
                                               Log_Processor.INFO)
                    if warning_video_out is not None:
                        warning_video_out.release()
                    return
                else:
                    # 预测视频帧获得结果
                    predict_result = self.predict(pre_source=frame, mode=mode,
                                                  show=False, iou=iou, conf=conf)
                    # 判断是否出现错误
                    warning_frame = False
                    # 全部识别模式和单个模型模式的出现错误的范围不同
                    if mode == 0:
                        type_keys = self.predict_class_type_num
                        if any(cls in predict_result[1][0].boxes.cls
                               for cls in type_keys) \
                                or any(cls in predict_result[2][0].boxes.cls
                                       for cls in type_keys) \
                                or any(cls in predict_result[3][0].boxes.cls
                                       for cls in type_keys):
                            warning_frame = True
                    else:
                        if any(cls in predict_result[mode][0].boxes.cls
                               for cls in self.predict_class_type_num):
                            warning_frame = True
                    # 出现错误时
                    if warning_frame:
                        # 全部识别模式保存检测框内图像并需要重新绘制图像
                        if mode == 0:
                            predict_result1 = predict_result[1][0]
                            predict_result2 = predict_result[2][0]
                            predict_result3 = predict_result[3][0]
                            # predict_result1.save_crop(save_dir)
                            # predict_result2.save_crop(save_dir)
                            # predict_result3.save_crop(save_dir)
                            predict_frame = self.three_model_plot(predict_result[1][0].orig_img,
                                                                  predict_result1, predict_result2,
                                                                  predict_result3)
                        # 单个模型识别模式保存检测框内图像并绘制图像
                        else:
                            # predict_result[mode][0].save_crop(save_dir)
                            predict_frame = predict_result[mode][0].plot()
                        # 放入图像
                        result_queue.put(predict_frame)
                        if not warning_flag:
                            warning_flag = True
                            # 利用VideoWriter保存有问题部分及前后的视频流，
                            # 文件路径为生成路径，帧率和分辨率统一为限制后的视频大小和帧率，彩色模式
                            fourcc = cv.VideoWriter.fourcc(*"DIVX")
                            save_name = datetime.datetime.now().strftime(Log_Processor.strftime_all)
                            warning_video_path = os.path.join(save_dir, f"{save_name}.avi")
                            warning_video_out = cv.VideoWriter(warning_video_path, fourcc, 30,
                                                               (predict_frame.shape[1],
                                                                predict_frame.shape[0]), True)
                            # 视频率写入
                            for save_frame in save_frame_deque:
                                warning_video_out.write(save_frame)
                        else:
                            warning_video_out.write(predict_frame)
                        no_warning_frame = 0
                        self.error_logger.log_write("Video Detector Warning!!", Log_Processor.ERROR)
                    # 无错误时，保存原始视频帧
                    else:
                        if mode == 0:
                            predict_frame = predict_result[1][0].orig_img
                        else:
                            predict_frame = predict_result[mode][0].orig_img
                        save_frame_deque.append(predict_frame)
                        # 检测前面出现问题时，当前是否经过了max_frame帧
                        if warning_flag:
                            result_queue.put(predict_frame)
                            if warning_video_out is not None:
                                warning_video_out.write(predict_frame)
                            no_warning_frame += 1
                            if no_warning_frame == max_frame:
                                warning_flag = False
                                warning_video_out.release()

            except Exception as e:
                # catch all errors and export to the log
                error_type = type(e).__name__
                ### 修改日志记录器的形式
                self.error_logger.logger.error("An error of type %s occurred: %s", error_type, str(e),
                                               exc_info=True)
                break

    def re_detect(self, video_file: str,
               mode: int = None,
               save_dir: str = None, max_frame: int = None,
               iou: float = None, conf: float = None) -> None:
        # 设置mode和save_dir，max_frame
        # iou和conf在self.predict里设置
        if mode is None:
            mode = self.model_mode
        if save_dir is None:
            save_dir = self.save_dir
        if not os.path.isabs(save_dir):
            save_dir = os.path.join(self.root_dir, save_dir)
        if max_frame is None:
            max_frame = self.max_frame

        predict_result = self.predict(pre_source=video_file, mode=mode,
                                      show=False, iou=iou, conf=conf)
        if mode == 0:
            for i, j, k in zip(predict_result[1], predict_result[2], predict_result[3]):
                pass
                # type_keys = self.predict_class_type_num
                # if any(cls in predict_result[1][0].boxes.cls
                #        for cls in type_keys) \
                #         or any(cls in predict_result[2][0].boxes.cls
                #                for cls in type_keys) \
                #         or any(cls in predict_result[3][0].boxes.cls
                #                for cls in type_keys):
                #     warning_frame = True
                # self.three_model_plot()

        else:
            for i in predict_result[mode]:
                pass


    ### 创建目录需要写入日志处理器，不再是静态方法
    def make_dir(self, file_path: str, caller_info: str = 'make_dir') -> None:
        """
        作用：
            创建一个空的目录

        参数:file_path(str):目录或者文件夹的绝对路径
        """
        try:
            # 获取目录路径
            directory = os.path.dirname(file_path)
            # 如果目录不存在，则创建目录
            if not os.path.exists(directory):
                os.makedirs(directory)
                ### 修改日志记录器的内容
                self.info_logger.logger.info(f"[{caller_info}] Directory '{directory}' created successfully.")
            else:
                print(f"Directory '{directory}' already exists.")
        except Exception as e:
            # catch all errors and export to the log
            error_type = type(e).__name__
            ### 修改日志记录器的形式
            self.error_logger.logger.error("An error of type %s occurred: %s", error_type, str(e),
                                           exc_info=True)

    ### 删除目录需要写入日志处理器，不再是静态方法
    def delete_file(self, directory: str):
        try:
            # 遍历目录中的所有文件
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                # 如果是文件则删除
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    ### 修改日志记录器的形式
                    self.info_logger.logger.info(f"File '{file_path}' removed successfully.")
            ### 修改日志记录器的形式
            self.info_logger.logger.info(f"All files in directory '{directory}' cleared successfully.")
        except Exception as e:
            ### 修改日志记录器的形式
            self.error_logger.logger.error(f"Failed to clear files in directory '{directory}'. Error: {e}")

    # 这个我不管了，自己改吧，注意你下面的内容
    def show_csv(self):
        """
        Metrics that display training results
        将训练完成后的各种评估参数画图画出来
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
    # device = Video_Detector.get_device()
    # 初始化参数
    # batch, epochs, project, name, imgsz, data, weight_pt = train_config.values()
    # model_mode, iou, conf, show, save_dir, max_frame = predict_config.values()

    # 初始化类实例
    video_detector = Video_Detector()

    # 查看结果
    for i in video_detector.__dict__.items():
        if i[0] != "model":
            print(i)

    # 调用类方法选择模型
    video_detector.select_default_model(1)
    # model.train()

    source = os.path.abspath("../../Model/test/fire.mp4")
    print(os.path.exists(source))
    Results_list = video_detector.predict(pre_source=source, mode=1)
    # for i in Results_list[1]:
    #     print(i)

