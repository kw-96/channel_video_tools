"""
视频水印标签页组件
支持静态/动态水印图片、不透明度、九宫格位置，输出保持原命名
"""
import os
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional, Callable

import customtkinter as ctk
import tkinter as tk

# 九宫格按钮文案与 position 键
POSITION_LABELS = [
    ("左上", "top_left"), ("上", "top"), ("右上", "top_right"),
    ("左", "left"), ("中", "center"), ("右", "right"),
    ("左下", "bottom_left"), ("下", "bottom"), ("右下", "bottom_right"),
]


class WatermarkTab:
    """视频水印标签页"""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        root: ctk.CTk,
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        self.parent = parent
        self.root = root
        self.log_callback = log_callback
        self.videos: list = []
        self.watermark_path: Optional[str] = None
        self.position = "center"
        self.is_processing = False
        self._create_ui()

    def _create_ui(self):
        """创建界面：先占位底部按钮与进度条，再放可伸缩的左右内容区"""
        # 底部进度条（先 pack 到 bottom，保证始终可见）
        prog_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        prog_frame.pack(side="bottom", fill="x", padx=10, pady=5)
        self.progress_var = tk.DoubleVar(value=0.0)
        ctk.CTkProgressBar(prog_frame, variable=self.progress_var, height=10).pack(
            fill="x", padx=10, pady=5
        )

        # 按钮行（紧贴进度条上方）
        buttons_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        buttons_frame.pack(side="bottom", fill="x", padx=10, pady=(5, 0))
        inner_btn = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        inner_btn.pack(anchor="center")
        self.start_btn = ctk.CTkButton(
            inner_btn, text="开始处理", command=self._start, width=120
        )
        self.start_btn.pack(side="left", padx=10, pady=5)
        ctk.CTkButton(inner_btn, text="重置", command=self._reset, width=120).pack(
            side="left", padx=10, pady=5
        )

        # 顶层：左右内容区（占据剩余空间）
        content_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        left_col = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 5))

        right_col = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True, padx=(5, 0))

        # 左侧第 1 行：水印图片
        wm_row = ctk.CTkFrame(left_col, fg_color="transparent")
        wm_row.pack(fill="x", pady=5)
        ctk.CTkLabel(
            wm_row,
            text="水印图片（支持静态/动态图）：",
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w", padx=10, pady=5)
        wm_sel = ctk.CTkFrame(wm_row, fg_color="transparent")
        wm_sel.pack(fill="x", padx=10, pady=5)
        self.watermark_var = tk.StringVar(value="")
        ctk.CTkEntry(
            wm_sel,
            textvariable=self.watermark_var,
            placeholder_text="请选择水印图片",
            state="readonly",
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(
            wm_sel, text="选择图片", command=self._select_watermark, width=100
        ).pack(side="left")

        # 左侧第 2 行：不透明度（滑块 + 输入框）
        opacity_row = ctk.CTkFrame(left_col, fg_color="transparent")
        opacity_row.pack(fill="x", pady=5)
        ctk.CTkLabel(
            opacity_row,
            text="水印不透明度（默认100%）：",
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w", padx=10, pady=5)
        bar_frame = ctk.CTkFrame(opacity_row, fg_color="transparent")
        bar_frame.pack(fill="x", padx=10, pady=5)
        self.opacity_var = tk.DoubleVar(value=100.0)
        self.opacity_slider = ctk.CTkSlider(
            bar_frame,
            from_=10,
            to=100,
            number_of_steps=9,
            variable=self.opacity_var,
            width=200,
            command=self._on_opacity_slider,
        )
        self.opacity_slider.pack(side="left", padx=(0, 10))
        self.opacity_entry = ctk.CTkEntry(bar_frame, width=60)
        self.opacity_entry.insert(0, "100")
        self.opacity_entry.pack(side="left", padx=5)
        ctk.CTkLabel(bar_frame, text="%").pack(side="left")
        self.opacity_entry.bind("<Return>", self._on_opacity_entry_return)
        self.opacity_entry.bind("<FocusOut>", self._on_opacity_entry_return)

        # 左侧第 3 行：水印位置（九宫格）
        pos_row = ctk.CTkFrame(left_col, fg_color="transparent")
        pos_row.pack(fill="both", expand=True, pady=5)
        ctk.CTkLabel(
            pos_row, text="水印位置：", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        grid_frame = ctk.CTkFrame(pos_row, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.position_btns = {}
        for i, (label, key) in enumerate(POSITION_LABELS):
            btn = ctk.CTkButton(
                grid_frame, text=label, width=70, command=lambda k=key: self._set_position(k)
            )
            btn.grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky="nsew")
            self.position_btns[key] = btn
        for r in range(3):
            grid_frame.grid_rowconfigure(r, weight=1)
        for c in range(3):
            grid_frame.grid_columnconfigure(c, weight=1)
        self._position_btn_normal = ("gray50", "gray25")
        self.position_btns["center"].configure(fg_color=("gray75", "gray30"))

        # 右侧第 1 行：待处理视频
        video_row = ctk.CTkFrame(right_col, fg_color="transparent")
        video_row.pack(fill="x", pady=5)
        ctk.CTkLabel(
            video_row, text="待处理视频：", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        btn_row = ctk.CTkFrame(video_row, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=5)
        self.video_count_label = ctk.CTkLabel(btn_row, text="已选择: 0 个文件")
        self.video_count_label.pack(side="left", padx=10)
        ctk.CTkButton(
            btn_row, text="选择视频", command=self._select_videos, width=100
        ).pack(side="left", padx=5)

        # 右侧第 2 行：输出目录
        out_row_container = ctk.CTkFrame(right_col, fg_color="transparent")
        out_row_container.pack(fill="x", pady=5)
        ctk.CTkLabel(
            out_row_container,
            text="输出目录（输出保持原命名）：",
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w", padx=10, pady=5)
        out_row = ctk.CTkFrame(out_row_container, fg_color="transparent")
        out_row.pack(fill="x", padx=10, pady=5)
        self.output_var = tk.StringVar(value="")
        ctk.CTkEntry(
            out_row,
            textvariable=self.output_var,
            placeholder_text="请选择输出目录",
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(
            out_row, text="浏览", command=self._select_output_dir, width=80
        ).pack(side="left")

        # 右侧第 3 行：处理日志
        log_row = ctk.CTkFrame(right_col, fg_color="transparent")
        log_row.pack(fill="both", expand=True, pady=5)
        ctk.CTkLabel(
            log_row, text="处理日志：", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        self.log_text = ctk.CTkTextbox(log_row, height=120, width=480)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)

        self._log("视频水印工具已就绪")

    def _log(self, msg: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        if self.log_callback:
            self.log_callback(msg)

    def _on_opacity_slider(self, v):
        self.opacity_entry.delete(0, "end")
        self.opacity_entry.insert(0, str(int(round(float(v)))))

    def _on_opacity_entry_return(self, event=None):
        try:
            val = int(self.opacity_entry.get().strip())
            val = max(10, min(100, val))
            self.opacity_var.set(float(val))
            self.opacity_entry.delete(0, "end")
            self.opacity_entry.insert(0, str(val))
        except (ValueError, tk.TclError):
            self.opacity_entry.delete(0, "end")
            self.opacity_entry.insert(0, str(int(self.opacity_var.get())))

    def _set_position(self, key: str):
        self.position_btns[self.position].configure(fg_color=self._position_btn_normal)
        self.position = key
        self.position_btns[key].configure(fg_color=("gray75", "gray30"))

    def _select_watermark(self):
        path = filedialog.askopenfilename(
            title="选择水印图片",
            filetypes=[("图片/GIF", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("所有", "*.*")]
        )
        if path:
            self.watermark_path = path
            self.watermark_var.set(os.path.basename(path))
            self._log(f"已选水印: {os.path.basename(path)}")

    def _select_videos(self):
        files = filedialog.askopenfilenames(
            title="选择要添加水印的视频",
            filetypes=[("视频", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm")]
        )
        if files:
            try:
                import sys
                src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if src_dir not in sys.path:
                    sys.path.insert(0, src_dir)
                from utils.video_watermark import VideoWatermark
                wm = VideoWatermark()
                added = [f for f in files if wm.is_supported_video(f) and f not in self.videos]
                self.videos.extend(added)
                self.video_count_label.configure(text=f"已选择: {len(self.videos)} 个文件")
                self._log(f"添加了 {len(added)} 个视频文件")
            except Exception as e:
                self._log(f"添加失败: {e}")
                messagebox.showerror("错误", str(e))

    def _select_output_dir(self):
        d = filedialog.askdirectory(title="选择输出目录")
        if d:
            self.output_var.set(d)
            self._log(f"输出目录: {d}")

    def _validate(self) -> bool:
        if not self.watermark_path or not os.path.isfile(self.watermark_path):
            messagebox.showwarning("警告", "请先选择水印图片")
            return False
        if not self.videos:
            messagebox.showwarning("警告", "请选择要添加水印的视频")
            return False
        if not self.output_var.get():
            messagebox.showwarning("警告", "请选择输出目录")
            return False
        return True

    def _start(self):
        if self.is_processing or not self._validate():
            return
        self.is_processing = True
        self.start_btn.configure(state="disabled")
        threading.Thread(target=self._process, daemon=True).start()

    def _process(self):
        try:
            import sys
            src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
            from utils.video_watermark import VideoWatermark
            wm = VideoWatermark()
            out_dir = self.output_var.get()
            opacity = max(0.1, min(1.0, float(self.opacity_var.get()) / 100.0))
            total = len(self.videos)

            def progress_cb(curr, n, name, pct, err):
                self.progress_var.set(((curr - 1) * 100 + pct) / n)
                if err:
                    self._log(f"[{curr}/{n}] {name} - 失败: {err[:80]}")
                elif pct >= 100:
                    self._log(f"[{curr}/{n}] {name} - 完成")

            results = wm.batch_apply(self.videos, out_dir, self.watermark_path, opacity, self.position, progress_cb)
            ok_count = sum(1 for s, _ in results.values() if s)
            fail_count = len(results) - ok_count
            self._log(f"完成。成功: {ok_count}, 失败: {fail_count}")
            messagebox.showinfo("完成", f"处理完成\n\n成功: {ok_count}\n失败: {fail_count}")
        except Exception as e:
            self._log(f"出错: {e}")
            messagebox.showerror("错误", str(e))
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.start_btn.configure(state="normal"))
            self.progress_var.set(100)

    def _reset(self):
        if self.is_processing:
            messagebox.showwarning("警告", "处理进行中，无法重置")
            return
        self.videos.clear()
        self.watermark_path = None
        self.watermark_var.set("")
        self.output_var.set("")
        self.video_count_label.configure(text="已选择: 0 个文件")
        self.progress_var.set(0.0)
        self.opacity_var.set(100.0)
        self.opacity_entry.delete(0, "end")
        self.opacity_entry.insert(0, "100")
        self._set_position("center")
        self.log_text.delete("1.0", "end")
        self._log("已重置所有设置")
