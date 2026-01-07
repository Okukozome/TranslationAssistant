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
    def __init__(self, root):
        self.root = root
        self.root.title("智能文字翻译助手")
        self.root.geometry("900x600")

        self.db = DatabaseManager()
        self.ai_service = TencentAIService()
        self.current_user_id = None

        pygame.mixer.init()
        self.show_login_frame()

    def show_login_frame(self):
        self.clear_frame()
        frame = tk.Frame(self.root)
        frame.pack(pady=100)

        tk.Label(frame, text="欢迎使用翻译助手", font=("Arial", 20)).pack(pady=20)

        tk.Label(frame, text="用户名:").pack()
        self.entry_user = tk.Entry(frame)
        self.entry_user.pack(pady=5)

        tk.Label(frame, text="密码:").pack()
        self.entry_pass = tk.Entry(frame, show="*")
        self.entry_pass.pack(pady=5)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="登录", command=self.login).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="注册", command=self.register).pack(side=tk.LEFT, padx=10)

    def login(self):
        username = self.entry_user.get()
        password = self.entry_pass.get()
        user_id = self.db.login_user(username, password)
        if user_id:
            self.current_user_id = user_id
            self.show_main_interface()
        else:
            messagebox.showerror("错误", "用户名或密码错误")

    def register(self):
        username = self.entry_user.get()
        password = self.entry_pass.get()
        if self.db.register_user(username, password):
            messagebox.showinfo("成功", "注册成功，请登录")
        else:
            messagebox.showerror("错误", "注册失败，用户名可能已存在")

    def show_main_interface(self):
        self.clear_frame()

        nav_frame = tk.Frame(self.root, bg="#ddd")
        nav_frame.pack(fill=tk.X)
        tk.Button(nav_frame, text="翻译主页", command=self.show_main_interface).pack(side=tk.LEFT, padx=10, pady=5)
        tk.Button(nav_frame, text="历史记录", command=self.show_history_interface).pack(side=tk.LEFT, padx=10, pady=5)
        tk.Button(nav_frame, text="退出登录", command=self.show_login_frame).pack(side=tk.RIGHT, padx=10, pady=5)

        content_frame = tk.Frame(self.root)
        content_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # UI Left
        left_frame = tk.LabelFrame(content_frame, text="1. 图片文字识别")
        left_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)

        btn_upload = tk.Button(left_frame, text="上传图片并识别 (OCR)", command=self.upload_and_ocr)
        btn_upload.pack(pady=10)

        self.lbl_image = tk.Label(left_frame, text="图片预览区域")
        self.lbl_image.pack(expand=True)

        # UI Right
        right_frame = tk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=5)

        tk.Label(right_frame, text="识别结果 / 待翻译文本:").pack(anchor="w")
        self.txt_source = tk.Text(right_frame, height=8)
        self.txt_source.pack(fill=tk.X, pady=5)

        setting_frame = tk.Frame(right_frame)
        setting_frame.pack(fill=tk.X, pady=10)
        tk.Label(setting_frame, text="目标语言:").pack(side=tk.LEFT)
        self.combo_lang = ttk.Combobox(setting_frame, values=list(LANG_MAP.keys()), state="readonly")
        self.combo_lang.current(1)
        self.combo_lang.pack(side=tk.LEFT, padx=5)
        tk.Button(setting_frame, text="开始翻译 (MT)", command=self.perform_translation).pack(side=tk.LEFT, padx=10)

        tk.Label(right_frame, text="翻译结果:").pack(anchor="w")
        self.txt_target = tk.Text(right_frame, height=8)
        self.txt_target.pack(fill=tk.X, pady=5)

        voice_frame = tk.Frame(right_frame)
        voice_frame.pack(fill=tk.X, pady=10)
        tk.Label(voice_frame, text="选择音色:").pack(side=tk.LEFT)
        self.combo_voice = ttk.Combobox(voice_frame, values=list(VOICE_MAP.keys()), state="readonly")
        self.combo_voice.current(0)
        self.combo_voice.pack(side=tk.LEFT, padx=5)
        tk.Button(voice_frame, text="语音播放 (TTS)", command=self.perform_tts).pack(side=tk.LEFT, padx=10)

    def show_history_interface(self):
        self.clear_frame()
        nav_frame = tk.Frame(self.root, bg="#ddd")
        nav_frame.pack(fill=tk.X)
        tk.Button(nav_frame, text="返回主页", command=self.show_main_interface).pack(side=tk.LEFT, padx=10, pady=5)

        list_frame = tk.Frame(self.root)
        list_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        columns = ("ID", "原文", "译文", "语言", "时间")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.heading("ID", text="ID");
        self.tree.column("ID", width=50)
        self.tree.heading("原文", text="原文");
        self.tree.column("原文", width=200)
        self.tree.heading("译文", text="译文");
        self.tree.column("译文", width=200)
        self.tree.heading("语言", text="语言")
        self.tree.heading("时间", text="时间")

        self.tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscroll=scrollbar.set)

        btn_del = tk.Button(self.root, text="删除选中记录", command=self.delete_selected_history)
        btn_del.pack(pady=10)
        self.load_history()

    def upload_and_ocr(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.bmp")])
        if file_path:
            load = Image.open(file_path)
            load.thumbnail((300, 300))
            render = ImageTk.PhotoImage(load)
            self.lbl_image.config(image=render, text="")
            self.lbl_image.image = render

            def run_ocr():
                self.txt_source.delete(1.0, tk.END);
                self.txt_source.insert(tk.END, "正在识别中...")
                text = self.ai_service.ocr_image(file_path)
                self.txt_source.delete(1.0, tk.END);
                self.txt_source.insert(tk.END, text)

            threading.Thread(target=run_ocr).start()

    def perform_translation(self):
        text = self.txt_source.get(1.0, tk.END).strip()
        if not text: return
        target_lang_name = self.combo_lang.get()
        target_code = LANG_MAP.get(target_lang_name, 'en')

        def run_trans():
            self.txt_target.delete(1.0, tk.END);
            self.txt_target.insert(tk.END, "正在翻译...")
            result = self.ai_service.translate_text(text, target_code)
            self.txt_target.delete(1.0, tk.END);
            self.txt_target.insert(tk.END, result)
            self.db.add_history(self.current_user_id, text, result, target_lang_name)

        threading.Thread(target=run_trans).start()

    def perform_tts(self):
        text = self.txt_target.get(1.0, tk.END).strip()
        if not text: return
        voice_id = VOICE_MAP.get(self.combo_voice.get(), 101001)

        def run_tts():
            file_path = self.ai_service.text_to_speech(text, voice_id)
            if file_path:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()

        threading.Thread(target=run_tts).start()

    def load_history(self):
        records = self.db.get_user_history(self.current_user_id)
        for item in self.tree.get_children(): self.tree.delete(item)
        for r in records: self.tree.insert("", "end", values=r)

    def delete_selected_history(self):
        selected = self.tree.selection()
        if not selected: return
        for item in selected:
            self.db.delete_history(self.tree.item(item)['values'][0])
            self.tree.delete(item)

    def clear_frame(self):
        for widget in self.root.winfo_children(): widget.destroy()