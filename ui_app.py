# ui_app.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from PIL import Image, ImageTk
import pygame

from database import DatabaseManager
from tencent_ai import TencentAIService
from config import LANG_MAP, VOICE_MAP


class TranslationApp:
    """
    UI 应用主类：负责管理整个程序的图形界面逻辑，
    包括用户登录注册、图片 OCR 识别、文字翻译及语音合成的交互流程。
    """

    def __init__(self, root):
        """
        初始化应用：设置主窗口、初始化数据库和 AI 服务实例。
        :param root: Tkinter 的根窗口对象
        """
        self.root = root
        self.root.title("智能文字翻译助手")
        self.root.geometry("900x600")

        # 初始化后端逻辑服务
        self.db = DatabaseManager()
        self.ai_service = TencentAIService()
        self.current_user_id = None  # 用于记录当前登录的用户 ID

        # 初始化音频混音器，用于播放合成的语音
        pygame.mixer.init()
        # 默认展示登录界面
        self.show_login_frame()

    def show_login_frame(self):
        """
        构建并展示登录/注册界面。
        """
        self.clear_frame()
        frame = tk.Frame(self.root)
        frame.pack(pady=100)

        tk.Label(frame, text="欢迎使用翻译助手", font=("Arial", 20)).pack(pady=20)

        # 账号输入区域
        tk.Label(frame, text="用户名:").pack()
        self.entry_user = tk.Entry(frame)
        self.entry_user.pack(pady=5)

        # 密码输入区域
        tk.Label(frame, text="密码:").pack()
        self.entry_pass = tk.Entry(frame, show="*")
        self.entry_pass.pack(pady=5)

        # 按钮区域
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="登录", command=self.login).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="注册", command=self.register).pack(side=tk.LEFT, padx=10)

    def login(self):
        """
        处理登录逻辑：验证用户信息并根据结果跳转界面。
        """
        username = self.entry_user.get()
        password = self.entry_pass.get()
        user_id = self.db.login_user(username, password)
        if user_id:
            self.current_user_id = user_id
            self.show_main_interface()
        else:
            messagebox.showerror("错误", "用户名或密码错误")

    def register(self):
        """
        处理注册逻辑：调用数据库接口创建新用户。
        """
        username = self.entry_user.get()
        password = self.entry_pass.get()
        if self.db.register_user(username, password):
            messagebox.showinfo("成功", "注册成功，请登录")
        else:
            messagebox.showerror("错误", "注册失败，用户名可能已存在")

    def show_main_interface(self):
        """
        构建并展示翻译主界面：包含 OCR 上传区、翻译设置区及结果展示区。
        """
        self.clear_frame()

        # 顶部导航栏
        nav_frame = tk.Frame(self.root, bg="#ddd")
        nav_frame.pack(fill=tk.X)
        tk.Button(nav_frame, text="翻译主页", command=self.show_main_interface).pack(side=tk.LEFT, padx=10, pady=5)
        tk.Button(nav_frame, text="历史记录", command=self.show_history_interface).pack(side=tk.LEFT, padx=10, pady=5)
        tk.Button(nav_frame, text="退出登录", command=self.show_login_frame).pack(side=tk.RIGHT, padx=10, pady=5)

        content_frame = tk.Frame(self.root)
        content_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # 左侧区域：OCR 图片文字识别
        left_frame = tk.LabelFrame(content_frame, text="1. 图片文字识别")
        left_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)

        btn_upload = tk.Button(left_frame, text="上传图片并识别 (OCR)", command=self.upload_and_ocr)
        btn_upload.pack(pady=10)

        self.lbl_image = tk.Label(left_frame, text="图片预览区域")
        self.lbl_image.pack(expand=True)

        # 右侧区域：翻译与 TTS
        right_frame = tk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=5)

        # 待翻译文本框
        tk.Label(right_frame, text="识别结果 / 待翻译文本:").pack(anchor="w")
        self.txt_source = tk.Text(right_frame, height=8)
        self.txt_source.pack(fill=tk.X, pady=5)

        # 语言选择与翻译按钮
        setting_frame = tk.Frame(right_frame)
        setting_frame.pack(fill=tk.X, pady=10)
        tk.Label(setting_frame, text="目标语言:").pack(side=tk.LEFT)
        self.combo_lang = ttk.Combobox(setting_frame, values=list(LANG_MAP.keys()), state="readonly")
        self.combo_lang.current(1)  # 默认选中英语
        self.combo_lang.pack(side=tk.LEFT, padx=5)
        tk.Button(setting_frame, text="开始翻译 (MT)", command=self.perform_translation).pack(side=tk.LEFT, padx=10)

        # 翻译结果展示框
        tk.Label(right_frame, text="翻译结果:").pack(anchor="w")
        self.txt_target = tk.Text(right_frame, height=8)
        self.txt_target.pack(fill=tk.X, pady=5)

        # 语音合成与播放
        voice_frame = tk.Frame(right_frame)
        voice_frame.pack(fill=tk.X, pady=10)
        tk.Label(voice_frame, text="选择音色:").pack(side=tk.LEFT)
        self.combo_voice = ttk.Combobox(voice_frame, values=list(VOICE_MAP.keys()), state="readonly")
        self.combo_voice.current(0)
        self.combo_voice.pack(side=tk.LEFT, padx=5)
        tk.Button(voice_frame, text="语音播放 (TTS)", command=self.perform_tts).pack(side=tk.LEFT, padx=10)

    def show_history_interface(self):
        """
        构建并展示历史记录界面，使用 Treeview 组件展示用户的翻译记录。
        """
        self.clear_frame()
        nav_frame = tk.Frame(self.root, bg="#ddd")
        nav_frame.pack(fill=tk.X)
        tk.Button(nav_frame, text="返回主页", command=self.show_main_interface).pack(side=tk.LEFT, padx=10, pady=5)

        list_frame = tk.Frame(self.root)
        list_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # 定义表格列
        columns = ("ID", "原文", "译文", "语言", "时间")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        # 设置列标题和宽度
        self.tree.heading("ID", text="ID");
        self.tree.column("ID", width=50)
        self.tree.heading("原文", text="原文");
        self.tree.column("原文", width=200)
        self.tree.heading("译文", text="译文");
        self.tree.column("译文", width=200)
        self.tree.heading("语言", text="语言")
        self.tree.heading("时间", text="时间")

        self.tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscroll=scrollbar.set)

        btn_del = tk.Button(self.root, text="删除选中记录", command=self.delete_selected_history)
        btn_del.pack(pady=10)

        # 加载数据库中的历史记录
        self.load_history()

    def upload_and_ocr(self):
        """
        处理图片上传并调用 OCR 服务。使用多线程防止 UI 界面卡顿。
        """
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.bmp")])
        if file_path:
            # 图片预览逻辑
            load = Image.open(file_path)
            load.thumbnail((300, 300))
            render = ImageTk.PhotoImage(load)
            self.lbl_image.config(image=render, text="")
            self.lbl_image.image = render

            # 定义异步 OCR 线程任务
            def run_ocr():
                self.txt_source.delete(1.0, tk.END)
                self.txt_source.insert(tk.END, "正在识别中...")
                text = self.ai_service.ocr_image(file_path)
                self.txt_source.delete(1.0, tk.END)
                self.txt_source.insert(tk.END, text)

            threading.Thread(target=run_ocr).start()

    def perform_translation(self):
        """
        执行文字翻译并保存至历史记录。使用多线程处理网络请求。
        """
        text = self.txt_source.get(1.0, tk.END).strip()
        if not text: return
        target_lang_name = self.combo_lang.get()
        target_code = LANG_MAP.get(target_lang_name, 'en')

        # 定义异步翻译线程任务
        def run_trans():
            self.txt_target.delete(1.0, tk.END)
            self.txt_target.insert(tk.END, "正在翻译...")
            result = self.ai_service.translate_text(text, target_code)
            self.txt_target.delete(1.0, tk.END)
            self.txt_target.insert(tk.END, result)
            # 翻译完成后自动存入数据库
            self.db.add_history(self.current_user_id, text, result, target_lang_name)

        threading.Thread(target=run_trans).start()

    def perform_tts(self):
        """
        执行语音合成并播放。使用多线程避免音频加载时阻塞界面。
        """
        text = self.txt_target.get(1.0, tk.END).strip()
        if not text: return
        voice_id = VOICE_MAP.get(self.combo_voice.get(), 101001)

        # 定义异步 TTS 线程任务
        def run_tts():
            file_path = self.ai_service.text_to_speech(text, voice_id)
            if file_path:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()

        threading.Thread(target=run_tts).start()

    def load_history(self):
        """
        从数据库读取当前用户的历史记录并填充到 Treeview 表格中。
        """
        records = self.db.get_user_history(self.current_user_id)
        # 清空当前表格内容
        for item in self.tree.get_children(): self.tree.delete(item)
        # 插入新记录
        for r in records: self.tree.insert("", "end", values=r)

    def delete_selected_history(self):
        """
        删除表格中选中的历史记录，并同步更新数据库。
        """
        selected = self.tree.selection()
        if not selected: return
        for item in selected:
            # values[0] 对应的是数据库中的记录 ID
            self.db.delete_history(self.tree.item(item)['values'][0])
            self.tree.delete(item)

    def clear_frame(self):
        """
        清空主窗口中的所有组件，用于切换不同界面视图。
        """
        for widget in self.root.winfo_children(): widget.destroy()