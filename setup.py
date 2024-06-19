from setuptools import setup, find_packages

setup(
    name='Home Security Surveillance',
    version='1.6.0',

    author="07xiaohei youyou Chai.h Captain",
    author_email="xiaohei07zhzhh@163.com",
    description= "A home security surveillance system",
    long_description="A home security surveillance system. "
                     "Use your various cameras for video visualization, recognition, and storage."
                     "The recognition function include fire recognition, "
                     "people recognition and fall people recognition.",
    license='GPLv3',    # 开源协议
    keywords=["pyhomess"],  # 命令
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests"]),  # 排除tests等
    include_package_data=True,  # 子目录搜索
    zip_safe=False,     # 解压安装
    install_requires=[
        "matplotlib>=3.2.2",
        "Pillow>=7.1.2",
        "numpy>=1.18.5",
        "ultralytics>=8.2.17",
        "ipython>=8.17.2",
        "torch>=1.8.0",
        "opencv_contrib_python>=4.6.0",
        "opencv_python>=4.6.0",
        "PyCameraList==1.0.0",
        "pygame>=2.4.0",
        "psutil>=5.8.0"
    ],  # 安装依赖
    entry_points={
        'console_scripts': [
            'pyhomess=home_security_surveillance.main:main',
        ],  # 命令行命令执行函数
    },
)
