"""
视频合并标签页组件
提供批量插入片头或片尾功能
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Callable, List
import os
import threading
from pathlib import Path


class MergeTab:
    """视频合并标签页"""
    
    def __init__(self,
                 parent: ctk.CTkFrame,
                 root: ctk.CTk,
                 log_callback: Optional[Callable[[str], None]] = None):
        """
        初始化视频合并标签页
        
        Args:
            parent: 父容器
            root: 根窗口
            log_callback: 日志回调函数
        """
        self.parent = parent
        self.root = root
        self.log_callback = log_callback
        
        # 文件列表
        self.main_videos = []
        self.insert_video = None
        self.insert_position = "head"  # "head" 或 "tail"
        
        # 处理状态
        self.is_processing = False
        
        # 创建UI
        self._create_ui()
    
    def _create_ui(self):
        """创建UI组件"""
        # 顶部行：主体视频（左） + 插入视频（右）
        top_row_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        top_row_frame.pack(fill="x", padx=10, pady=5)

        top_left_frame = ctk.CTkFrame(top_row_frame, fg_color="transparent")
        top_left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        top_right_frame = ctk.CTkFrame(top_row_frame, fg_color="transparent")
        top_right_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self._create_main_videos_section(top_left_frame)
        self._create_insert_video_section(top_right_frame)

        # 中间行：插入位置（左） + 输出目录（右）
        middle_row_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        middle_row_frame.pack(fill="x", padx=10, pady=5)

        middle_left_frame = ctk.CTkFrame(middle_row_frame, fg_color="transparent")
        middle_left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        middle_right_frame = ctk.CTkFrame(middle_row_frame, fg_color="transparent")
        middle_right_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self._create_position_section(middle_left_frame)
        self._create_output_section(middle_right_frame)

        self._create_progress_section()
        self._create_log_button_section()
        self._log("视频合并工具已就绪")
    
    def _create_main_videos_section(self, parent):
        """创建主体视频选择区域"""
        main_videos_frame = ctk.CTkFrame(parent, fg_color="transparent")
        main_videos_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            main_videos_frame,
            text="主体视频（多个）:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        select_frame = ctk.CTkFrame(main_videos_frame, fg_color="transparent")
        select_frame.pack(fill="x", padx=10, pady=5)
        
        self.main_videos_count_label = ctk.CTkLabel(
            select_frame,
            text="已选择: 0 个文件"
        )
        self.main_videos_count_label.pack(side="left", padx=10)
        
        ctk.CTkButton(
            select_frame,
            text="选择视频",
            command=self._select_main_videos,
            width=120
        ).pack(side="left", padx=5)
    
    def _create_insert_video_section(self, parent):
        """创建插入视频选择区域"""
        insert_video_frame = ctk.CTkFrame(parent, fg_color="transparent")
        insert_video_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            insert_video_frame,
            text="插入视频（片头/片尾，单个）:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        select_frame = ctk.CTkFrame(insert_video_frame, fg_color="transparent")
        select_frame.pack(fill="x", padx=10, pady=5)
        
        self.insert_video_var = tk.StringVar(value="")
        insert_video_entry = ctk.CTkEntry(
            select_frame,
            textvariable=self.insert_video_var,
            placeholder_text="请选择要插入的视频文件",
            state="readonly"
        )
        insert_video_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(
            select_frame,
            text="选择文件",
            command=self._select_insert_video,
            width=120
        ).pack(side="left")
    
    def _create_position_section(self, parent):
        """创建插入位置选择区域"""
        position_frame = ctk.CTkFrame(parent, fg_color="transparent")
        position_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            position_frame,
            text="插入位置:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        select_frame = ctk.CTkFrame(position_frame, fg_color="transparent")
        select_frame.pack(fill="x", padx=10, pady=5)
        
        self.position_var = tk.StringVar(value="head")
        ctk.CTkRadioButton(
            select_frame,
            text="片头（插入视频在前）",
            variable=self.position_var,
            value="head",
            command=self._on_position_changed
        ).pack(side="left", padx=10)
        
        ctk.CTkRadioButton(
            select_frame,
            text="片尾（插入视频在后）",
            variable=self.position_var,
            value="tail",
            command=self._on_position_changed
        ).pack(side="left", padx=10)
    
    def _create_output_section(self, parent):
        """创建输出目录选择区域"""
        output_frame = ctk.CTkFrame(parent, fg_color="transparent")
        output_frame.pack(fill="x", pady=5)
        
        # 标题行：输出目录 + 保持原命名勾选框
        title_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            title_frame,
            text="输出目录:",
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left")
        
        self.keep_original_name_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            title_frame,
            text="保持输出文件原命名",
            variable=self.keep_original_name_var
        ).pack(side="left", padx=(10, 0))
        
        select_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        select_frame.pack(fill="x", padx=10, pady=5)
        
        self.output_var = tk.StringVar(value="")
        output_entry = ctk.CTkEntry(
            select_frame,
            textvariable=self.output_var,
            placeholder_text="请选择输出目录"
        )
        output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(
            select_frame,
            text="浏览",
            command=self._select_output_dir,
            width=100
        ).pack(side="left")
    
    def _create_progress_section(self):
        """创建进度条区域"""
        progress_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        progress_frame.pack(fill="x", padx=10, pady=(5, 5), side="bottom")
        
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            variable=self.progress_var,
            height=10
        )
        self.progress_bar.pack(fill="x", padx=10, pady=5)
    
    def _create_log_button_section(self):
        """创建日志和按钮区域"""
        log_button_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        log_button_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self._create_log_section(log_button_frame)
        self._create_button_section(log_button_frame)
    
    def _create_log_section(self, parent):
        """创建日志区域"""
        log_frame = ctk.CTkFrame(parent, fg_color="transparent")
        log_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            log_frame,
            text="处理日志:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        self.log_text = ctk.CTkTextbox(log_frame, height=200, width=500)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
    
    def _create_button_section(self, parent):
        """创建按钮区域"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(side="right", fill="y", padx=(10, 0))
        
        top_spacer = ctk.CTkFrame(button_frame, fg_color="transparent", height=45)
        top_spacer.pack(fill="x")
        
        self.start_button = ctk.CTkButton(
            button_frame,
            text="开始处理",
            command=self._start_processing,
            width=150,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.start_button.pack(pady=(0, 10))
        
        self.reset_button = ctk.CTkButton(
            button_frame,
            text="重置",
            command=self._reset,
            width=150,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="gray",
            hover_color="darkgray"
        )
        self.reset_button.pack()
    
    def _log(self, message: str):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        if self.log_callback:
            self.log_callback(message)
    
    def _select_main_videos(self):
        """选择主体视频文件"""
        files = filedialog.askopenfilenames(
            title="选择主体视频文件",
            filetypes=[("视频文件", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm")]
        )
        if files:
            # 导入视频合并器以检查格式
            try:
                import sys
                import os
                src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if src_dir not in sys.path:
                    sys.path.insert(0, src_dir)
                from utils.video_merger import VideoMerger
                merger = VideoMerger()
                
                added_count = 0
                for f in files:
                    if f not in self.main_videos and merger.is_supported_format(f):
                        self.main_videos.append(f)
                        added_count += 1
                
                self._update_main_videos_count()
                self._log(f"添加了 {added_count} 个主体视频文件")
            except Exception as e:
                self._log(f"添加文件失败: {e}")
                messagebox.showerror("错误", f"添加文件失败: {e}")
    
    def _select_insert_video(self):
        """选择插入视频文件"""
        file = filedialog.askopenfilename(
            title="选择要插入的视频文件",
            filetypes=[("视频文件", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm")]
        )
        if file:
            try:
                import sys
                import os
                src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if src_dir not in sys.path:
                    sys.path.insert(0, src_dir)
                from utils.video_merger import VideoMerger
                merger = VideoMerger()
                
                if merger.is_supported_format(file):
                    self.insert_video = file
                    self.insert_video_var.set(os.path.basename(file))
                    self._log(f"选择插入视频: {os.path.basename(file)}")
                else:
                    messagebox.showwarning("警告", "不支持的视频格式")
            except Exception as e:
                self._log(f"选择文件失败: {e}")
                messagebox.showerror("错误", f"选择文件失败: {e}")
    
    def _select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_var.set(directory)
            self._log(f"选择输出目录: {directory}")
    
    def _on_position_changed(self):
        """插入位置改变回调"""
        self.insert_position = self.position_var.get()
        position_text = "片头" if self.insert_position == "head" else "片尾"
        self._log(f"插入位置已设置为: {position_text}")
    
    def _update_main_videos_count(self):
        """更新主体视频数量显示"""
        self.main_videos_count_label.configure(text=f"已选择: {len(self.main_videos)} 个文件")
    
    def _validate_inputs(self) -> bool:
        """验证输入参数"""
        if not self.main_videos:
            messagebox.showwarning("警告", "请先选择主体视频文件")
            return False
        if not self.insert_video:
            messagebox.showwarning("警告", "请选择要插入的视频文件")
            return False
        if not self.output_var.get():
            messagebox.showwarning("警告", "请选择输出目录")
            return False
        return True
    
    def _start_processing(self):
        """开始处理视频"""
        if self.is_processing or not self._validate_inputs():
            return
        
        self.is_processing = True
        self.start_button.configure(state="disabled")
        thread = threading.Thread(target=self._process_videos)
        thread.daemon = True
        thread.start()
    
    def _process_videos(self):
        """处理视频（后台线程）"""
        try:
            import sys
            import os
            src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
            from utils.video_merger import VideoMerger
            
            merger = VideoMerger()
            output_dir = self.output_var.get()
            insert_position = self.position_var.get()
            position_text = "片头" if insert_position == "head" else "片尾"
            keep_original_name = getattr(self, "keep_original_name_var", None)
            keep_original_name = bool(keep_original_name.get()) if keep_original_name else False
            
            self._log(f"开始处理 {len(self.main_videos)} 个视频")
            self._log(f"插入位置: {position_text}")
            
            def progress_cb(curr, total, name, prog, err):
                self.progress_var.set(((curr - 1) * 100 + prog) / total)
                if err:
                    msg = f"[{curr}/{total}] {name} - 失败 (错误: {err[:50]})"
                elif prog >= 100:
                    msg = f"[{curr}/{total}] {name} - 完成"
                else:
                    msg = f"[{curr}/{total}] {name} - 处理中 ({prog:.1f}%)"
                self._log(msg)
            
            # 根据勾选状态决定输出命名规则
            if keep_original_name:
                # 保持输出文件原命名
                results = {}
                total = len(self.main_videos)
                for idx, main_video in enumerate(self.main_videos, 1):
                    filename = Path(main_video).stem
                    ext = Path(main_video).suffix or ".mp4"
                    output_filename = f"{filename}{ext}"
                    output_path = os.path.join(output_dir, output_filename)

                    def file_progress(percent, curr_idx=idx, total_count=total, name=filename):
                        if percent is None:
                            return
                        progress_cb(curr_idx, total_count, name, percent, "")

                    success, error = merger.merge_videos(
                        main_video,
                        self.insert_video,
                        output_path,
                        insert_position,
                        file_progress
                    )

                    # 统一使用进度回调输出最终状态
                    error_msg = error if not success else ""
                    progress_cb(idx, total, filename, 100.0, error_msg)

                    results[main_video] = (success, error)
            else:
                # 默认行为：按序号命名输出文件
                results = merger.batch_merge(
                    self.main_videos,
                    self.insert_video,
                    output_dir,
                    insert_position,
                    progress_cb
                )
            
            self._handle_merge_results(results)
            
        except Exception as e:
            self._log(f"出错: {e}")
            messagebox.showerror("错误", f"处理出错:\n{e}")
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.start_button.configure(state="normal"))
    
    def _handle_merge_results(self, results: dict):
        """处理合并结果"""
        success_count = sum(1 for success, _ in results.values() if success)
        failed_count = len(results) - success_count
        failed_files = [
            (os.path.basename(k), e) for k, (s, e) in results.items() if not s
        ]
        
        self._log(f"完成! 成功: {success_count}, 失败: {failed_count}")
        if failed_files:
            self._log("失败文件:")
            for fname, err in failed_files:
                self._log(f"  - {fname}: {err[:100] if err else '未知错误'}")
        
        self.progress_var.set(100)
        messagebox.showinfo(
            "完成",
            f"处理完成!\n\n成功: {success_count}\n失败: {failed_count}"
        )
    
    def _reset(self):
        """重置视频合并工具"""
        if self.is_processing:
            messagebox.showwarning("警告", "处理进行中，无法重置")
            return
        
        # 清空文件列表
        self.main_videos.clear()
        self.insert_video = None
        self.insert_video_var.set("")
        self._update_main_videos_count()
        
        # 重置输出目录
        self.output_var.set("")
        
        # 重置插入位置
        self.position_var.set("head")
        self.insert_position = "head"
        
        # 重置进度条
        self.progress_var.set(0.0)
        
        # 清空日志
        self.log_text.delete("1.0", "end")
        
        # 记录重置操作
        self._log("已重置所有设置")
