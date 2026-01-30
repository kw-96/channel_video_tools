"""
视频规范标签页组件
批量将视频统一为目标分辨率（横版/竖版），保持宽高比并填充黑边
"""
import os
import threading
from tkinter import filedialog, messagebox
from typing import Optional, Callable

import customtkinter as ctk
import tkinter as tk


class NormalizerTab:
    """视频规范标签页"""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        root: ctk.CTk,
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        self.parent = parent
        self.root = root
        self.log_callback = log_callback
        self.input_files = []
        self.is_processing = False
        try:
            from utils.video_normalizer import VideoNormalizer
            self.normalizer = VideoNormalizer()
        except ImportError as e:
            self.normalizer = None
            ctk.CTkLabel(
                parent, text=f"视频规范工具初始化失败: {e}",
                font=ctk.CTkFont(size=12), text_color="red"
            ).pack(pady=20)
            return
        self._create_ui()
        self._log("视频规范工具已就绪")
        if self.normalizer.has_ffprobe:
            self._log("支持详细进度显示")
        else:
            self._log("警告: 未找到ffprobe，将无法显示详细进度")

    def _create_ui(self):
        top = ctk.CTkFrame(self.parent, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=5)
        left_f = ctk.CTkFrame(top, fg_color="transparent")
        left_f.pack(side="left", fill="both", expand=True, padx=(0, 5))
        ctk.CTkLabel(left_f, text="输入文件:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        btn_f = ctk.CTkFrame(left_f, fg_color="transparent")
        btn_f.pack(fill="x", padx=10, pady=5)
        self.file_count_label = ctk.CTkLabel(btn_f, text="已选择: 0 个文件")
        self.file_count_label.pack(side="left", padx=10)
        ctk.CTkButton(btn_f, text="选择视频", command=self._select_videos, width=120).pack(side="left", padx=5)
        right_f = ctk.CTkFrame(top, fg_color="transparent")
        right_f.pack(side="left", fill="both", expand=True, padx=(5, 0))
        ctk.CTkLabel(right_f, text="输出设置:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        out_f = ctk.CTkFrame(right_f, fg_color="transparent")
        out_f.pack(fill="x", padx=10, pady=5)
        self.output_var = tk.StringVar(value="")
        ctk.CTkEntry(out_f, textvariable=self.output_var, placeholder_text="请选择输出目录").pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(out_f, text="浏览", command=self._select_output, width=100).pack(side="left")
        param_f = ctk.CTkFrame(self.parent, fg_color="transparent")
        param_f.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(param_f, text="处理参数:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        row1 = ctk.CTkFrame(param_f, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row1, text="目标宽度:").pack(side="left", padx=5)
        self.width_var = tk.IntVar(value=1920)
        ctk.CTkEntry(row1, textvariable=self.width_var, width=100).pack(side="left", padx=5)
        ctk.CTkLabel(row1, text="目标高度:").pack(side="left", padx=5)
        self.height_var = tk.IntVar(value=1080)
        ctk.CTkEntry(row1, textvariable=self.height_var, width=100).pack(side="left", padx=5)
        ctk.CTkLabel(row1, text="填充颜色:").pack(side="left", padx=5)
        self.color_var = tk.StringVar(value="black")
        ctk.CTkOptionMenu(row1, values=["black", "white", "gray", "blue", "red", "green"], variable=self.color_var, width=100).pack(side="left", padx=5)
        prog_f = ctk.CTkFrame(self.parent, fg_color="transparent")
        prog_f.pack(side="bottom", fill="x", padx=10, pady=5)
        self.progress_var = tk.DoubleVar(value=0.0)
        ctk.CTkProgressBar(prog_f, variable=self.progress_var, height=10).pack(fill="x", padx=10, pady=5)
        log_btn_f = ctk.CTkFrame(self.parent, fg_color="transparent")
        log_btn_f.pack(fill="both", expand=True, padx=10, pady=5)
        log_f = ctk.CTkFrame(log_btn_f, fg_color="transparent")
        log_f.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(log_f, text="处理日志:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        self.log_text = ctk.CTkTextbox(log_f, height=180, width=500)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
        btn_f2 = ctk.CTkFrame(log_btn_f, fg_color="transparent")
        btn_f2.pack(side="right", fill="y")
        ctk.CTkFrame(btn_f2, fg_color="transparent", height=45).pack(fill="x")
        self.start_btn = ctk.CTkButton(btn_f2, text="开始处理", command=self._start, width=150, height=45, font=ctk.CTkFont(size=14, weight="bold"))
        self.start_btn.pack(pady=(0, 10))
        ctk.CTkButton(btn_f2, text="重置", command=self._reset, width=150, height=45, font=ctk.CTkFont(size=14, weight="bold"), fg_color="gray", hover_color="darkgray").pack()

    def _log(self, msg: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        if self.log_callback:
            self.log_callback(msg)

    def _select_videos(self):
        choice = messagebox.askquestion("选择方式", "选择文件夹还是文件？\n\n\"是\" - 文件夹\n\"否\" - 文件", icon="question")
        if choice == "yes":
            folder = filedialog.askdirectory(title="选择包含视频的文件夹")
            if folder:
                count = 0
                for root, _, files in os.walk(folder):
                    for f in files:
                        path = os.path.join(root, f)
                        if path not in self.input_files and self.normalizer.is_supported_format(path):
                            self.input_files.append(path)
                            count += 1
                self.file_count_label.configure(text=f"已选择: {len(self.input_files)} 个文件")
                self._log(f"从文件夹添加了 {count} 个视频")
        else:
            files = filedialog.askopenfilenames(title="选择视频文件", filetypes=[("视频文件", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm")])
            if files:
                for f in files:
                    if f not in self.input_files and self.normalizer.is_supported_format(f):
                        self.input_files.append(f)
                self.file_count_label.configure(text=f"已选择: {len(self.input_files)} 个文件")
                self._log(f"添加了 {len(files)} 个文件")

    def _select_output(self):
        d = filedialog.askdirectory(title="选择输出目录")
        if d:
            self.output_var.set(d)

    def _validate(self) -> bool:
        if not self.input_files:
            messagebox.showwarning("警告", "请先选择要处理的视频文件")
            return False
        if not self.output_var.get():
            messagebox.showwarning("警告", "请选择输出目录")
            return False
        w, h = self.width_var.get(), self.height_var.get()
        if w == h:
            messagebox.showerror("错误", "暂不支持正方形尺寸（宽度=高度）")
            return False
        if w <= 0 or h <= 0:
            messagebox.showerror("错误", "宽度和高度必须大于 0")
            return False
        return True

    def _start(self):
        if not self.normalizer or self.is_processing or not self._validate():
            return
        self.is_processing = True
        self.start_btn.configure(state="disabled")
        threading.Thread(target=self._process, daemon=True).start()

    def _process(self):
        try:
            out_dir = self.output_var.get()
            w, h = self.width_var.get(), self.height_var.get()
            pad = self.color_var.get()
            total = len(self.input_files)
            self._log(f"开始处理 {total} 个视频")
            self._log(f"目标尺寸: {w}x{h}")

            def progress_cb(curr, n, name, prog, act, err):
                self.progress_var.set(((curr - 1) * 100 + prog) / n)
                if act:
                    msg = f"[{curr}/{n}] {name} - " + {"copied": "已复制", "processed": "已转换", "failed": "失败"}.get(act, "处理中")
                    if err:
                        msg += f" (错误: {err[:50]})"
                    self._log(msg)

            results = self.normalizer.batch_normalize(self.input_files, out_dir, w, h, pad, progress_cb)
            succ = sum(1 for s, _, _ in results.values() if s)
            copied = sum(1 for s, a, _ in results.values() if s and a == "copied")
            processed = sum(1 for s, a, _ in results.values() if s and a == "processed")
            failed = len(results) - succ
            self._log(f"完成! 成功:{succ}(复制:{copied},转换:{processed}),失败:{failed}")
            messagebox.showinfo("完成", f"处理完成!\n\n成功: {succ}\n  复制: {copied}\n  转换: {processed}\n失败: {failed}")
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
        self.input_files.clear()
        self.file_count_label.configure(text="已选择: 0 个文件")
        self.output_var.set("")
        self.width_var.set(1920)
        self.height_var.set(1080)
        self.color_var.set("black")
        self.progress_var.set(0.0)
        self.log_text.delete("1.0", "end")
        self._log("已重置所有设置")
