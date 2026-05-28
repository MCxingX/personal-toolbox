"""API Key 设置对话框."""

import tkinter as tk
from tkinter import ttk, messagebox


class SettingsDialog:
    """API Key 设置对话框."""

    def __init__(self, parent, settings_db):
        self.parent = parent
        self.settings_db = settings_db
        self.dialog = None

    def show(self):
        """显示设置对话框."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("API 设置")
        self.dialog.geometry("500x300")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 标题
        tk.Label(
            self.dialog, text="第三方 API Key 配置",
            font=("微软雅黑", 14, "bold")
        ).pack(pady=(20, 10))

        # 说明
        tk.Label(
            self.dialog,
            text="以下 API Key 仅存储在您的本地数据库中，不会上传到任何服务器。\n留空表示不启用该数据源。",
            fg="gray", font=("微软雅黑", 9)
        ).pack(pady=(0, 20))

        # TopHub API Key
        tophub_frame = tk.Frame(self.dialog, padx=20)
        tophub_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            tophub_frame, text="TopHub API Key:",
            font=("微软雅黑", 10), width=15, anchor=tk.W
        ).pack(side=tk.LEFT)

        tophub_var = tk.StringVar(value=self.settings_db.get("tophub_api_key", ""))
        tophub_entry = ttk.Entry(tophub_frame, textvariable=tophub_var, width=35, show="*")
        tophub_entry.pack(side=tk.LEFT, padx=5)

        # 显示/隐藏按钮
        def toggle_visibility():
            if tophub_entry.cget("show") == "*":
                tophub_entry.config(show="")
                show_btn.config(text="隐藏")
            else:
                tophub_entry.config(show="*")
                show_btn.config(text="显示")

        show_btn = tk.Button(tophub_frame, text="显示", command=toggle_visibility)
        show_btn.pack(side=tk.LEFT, padx=5)

        # 按钮区域
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(pady=30)

        def save_and_close():
            self.settings_db.set("tophub_api_key", tophub_var.get().strip())
            messagebox.showinfo("提示", "设置已保存！", parent=self.dialog)
            self.dialog.destroy()

        tk.Button(
            btn_frame, text="保存", width=10,
            command=save_and_close, bg="#1890ff", fg="white",
            font=("微软雅黑", 10)
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame, text="取消", width=10,
            command=self.dialog.destroy,
            font=("微软雅黑", 10)
        ).pack(side=tk.LEFT, padx=10)
