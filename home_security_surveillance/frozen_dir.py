# 获得项目根路径
# 根据是否打包做区分
import os
import sys
if getattr(sys, 'frozen', False):
    # 打包后的路径
    project_dir = os.path.dirname(sys.executable)
else:
    project_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))