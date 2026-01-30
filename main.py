"""
渠道视频批量处理工具 - 程序入口
包含视频规范、视频水印、视频合并及主题设置
"""
import sys
from pathlib import Path

# 保证可导入 src 下模块
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

import customtkinter as ctk
from gui.main_window import ChannelVideoToolsGUI

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = ChannelVideoToolsGUI(config_dir=str(_root / "config"))
    app.run()
