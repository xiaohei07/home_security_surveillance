from home_security_surveillance import *
# 主循环函数，用于外界的使用
def main():
    root = tk.Tk()
    app = VideoMonitorApp(root)
    app.root.mainloop()

# 接口，main可用于命令行调用
if __name__ == "__main__":
    main()
