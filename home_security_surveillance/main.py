from home_security_surveillance import *

# 主循环函数，用于外界的使用
def main():
    # 由于exe可能在不同的操作环境中
    # 打包前必须检查当前脚本是否运行在“冻结”（即打包）的环境中
    multiprocessing.freeze_support()

    app = VideoMonitorApp(tk.Tk())
    app.root.after(ms=1000, func=app.check_video_processor)
    app.root.mainloop()

# 接口，main可用于命令行调用
if __name__ == "__main__":
    main()