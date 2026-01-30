"""
渠道视频批量处理工具 - 主窗口
仅包含：视频规范、视频水印、视频合并；右上角圆形主题切换（Canvas 绘制）
"""
import sys
from pathlib import Path

import customtkinter as ctk
import tkinter as tk


class ChannelVideoToolsGUI:
    """渠道视频批量处理工具主窗口"""

    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.root = ctk.CTk()
        self.root.title("渠道视频批量处理工具")
        self.root.geometry("820x520")
        self._init_theme()
        self.create_widgets()

    def _init_theme(self):
        """从配置加载主题并应用"""
        try:
            from config.settings import ThemeSettingsManager
            self.theme_manager = ThemeSettingsManager(self.config_dir)
            mode = self.theme_manager.get_theme_setting()
            if mode == "system":
                mode = "dark"
            ctk.set_appearance_mode(mode)
        except Exception:
            self.theme_manager = None

    def _toggle_theme(self):
        """在深色与浅色间切换主题并持久化，并更新按钮图标"""
        current = ctk.get_appearance_mode()
        if current == "Dark":
            next_mode = "light"
        else:
            next_mode = "dark"
        ctk.set_appearance_mode(next_mode)
        if self.theme_manager:
            self.theme_manager.set_theme_setting(next_mode)
        self._update_theme_button_icon()

    def _get_theme_icons(self):
        """获取主题切换用太阳/月亮 CTkImage，失败时返回 (None, None)"""
        try:
            from gui.theme_icons import get_theme_button_images
            return get_theme_button_images(size=(24, 24))
        except Exception:
            return None, None

    def _theme_bg_color(self):
        """当前主题对应的背景色，与 CTk 根窗口一致（blue 主题：gray14/gray92）"""
        return "gray14" if ctk.get_appearance_mode() == "Dark" else "gray92"

    def _theme_hover_color(self):
        """当前主题对应的悬停色"""
        return "gray25" if ctk.get_appearance_mode() == "Dark" else "gray75"

    def _update_theme_button_icon(self):
        """根据当前主题更新主题按钮图标或文案：深色显示太阳（切到浅色），浅色显示月亮（切到深色）"""
        current = ctk.get_appearance_mode()
        if self._sun_ctk is not None and self._moon_ctk is not None:
            self._theme_btn_label.configure(
                image=self._sun_ctk if current == "Dark" else self._moon_ctk,
                text="",
            )
        else:
            self._theme_btn_label.configure(
                image=None,
                text="切换到浅色" if current == "Dark" else "切换到深色",
            )
        if hasattr(self, "_theme_canvas") and self._theme_canvas.winfo_exists():
            bg = self._theme_bg_color()
            self._theme_canvas.configure(bg=bg)
            self._theme_canvas.itemconfig(self._theme_oval_id, fill=bg, outline=bg)

    def _on_theme_btn_enter(self, event=None):
        if hasattr(self, "_theme_canvas") and self._theme_canvas.winfo_exists():
            c = self._theme_hover_color()
            self._theme_canvas.itemconfig(self._theme_oval_id, fill=c, outline=c)

    def _on_theme_btn_leave(self, event=None):
        if hasattr(self, "_theme_canvas") and self._theme_canvas.winfo_exists():
            c = self._theme_bg_color()
            self._theme_canvas.itemconfig(self._theme_oval_id, fill=c, outline=c)

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabview = ctk.CTkTabview(
            main_frame,
            width=800,
            height=460,
            corner_radius=15,
            border_width=2,
        )
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tabview.add("视频规范")
        self.tabview.add("视频水印")
        self.tabview.add("视频合并")
        self._ensure_src_in_path()
        self.create_normalizer_tab()
        self.create_watermark_tab()
        self.create_merge_tab()
        self._sun_ctk, self._moon_ctk = self._get_theme_icons()
        current_mode = ctk.get_appearance_mode()
        initial_image = self._sun_ctk if current_mode == "Dark" else self._moon_ctk
        _size = 40
        _pad = 2
        _bg = self._theme_bg_color()
        parent = self.root
        self._theme_canvas = tk.Canvas(
            parent,
            width=_size,
            height=_size,
            bg=_bg,
            highlightthickness=0,
        )
        self._theme_canvas.place(relx=1, rely=0, anchor="ne", x=-15, y=20)
        self._theme_oval_id = self._theme_canvas.create_oval(
            _pad, _pad, _size - _pad, _size - _pad,
            fill=_bg,
            outline=_bg,
        )
        self._theme_btn_label = ctk.CTkLabel(
            parent,
            text="" if initial_image else ("切换到浅色" if current_mode == "Dark" else "切换到深色"),
            image=initial_image,
            fg_color="transparent",
            width=_size - 8,
            height=_size - 8,
        )
        self._theme_btn_label.place(relx=1, rely=0, anchor="center", x=-_size // 2 - 15, y=_size // 2 + 20)
        for w in (self._theme_canvas, self._theme_btn_label):
            w.bind("<Button-1>", lambda e: self._toggle_theme())
            w.configure(cursor="hand2")
        self._theme_canvas.bind("<Enter>", self._on_theme_btn_enter)
        self._theme_canvas.bind("<Leave>", self._on_theme_btn_leave)
        self._theme_btn_label.bind("<Enter>", self._on_theme_btn_enter)
        self._theme_btn_label.bind("<Leave>", self._on_theme_btn_leave)

    def _ensure_src_in_path(self):
        """确保 src 目录在 sys.path 中，便于各标签页导入 utils"""
        src_dir = str(Path(__file__).resolve().parent)
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

    def create_normalizer_tab(self):
        frame = self.tabview.tab("视频规范")
        try:
            from gui.normalizer_tab import NormalizerTab
            NormalizerTab(parent=frame, root=self.root)
        except Exception as e:
            ctk.CTkLabel(frame, text=f"视频规范初始化失败: {e}", font=ctk.CTkFont(size=12), text_color="red").pack(pady=20)

    def create_watermark_tab(self):
        frame = self.tabview.tab("视频水印")
        try:
            from gui.watermark_tab import WatermarkTab
            WatermarkTab(parent=frame, root=self.root)
        except Exception as e:
            ctk.CTkLabel(frame, text=f"视频水印初始化失败: {e}", font=ctk.CTkFont(size=12), text_color="red").pack(pady=20)

    def create_merge_tab(self):
        frame = self.tabview.tab("视频合并")
        try:
            from gui.merge_tab import MergeTab
            MergeTab(parent=frame, root=self.root)
        except Exception as e:
            ctk.CTkLabel(frame, text=f"视频合并初始化失败: {e}", font=ctk.CTkFont(size=12), text_color="red").pack(pady=20)

    def run(self):
        self.root.mainloop()
