# main.py
import tkinter as tk
from ui_app import TranslationApp

if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()

    # 实例化应用
    app = TranslationApp(root)

    # 进入主循环
    root.mainloop()