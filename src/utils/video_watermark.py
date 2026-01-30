"""
视频水印核心处理模块
支持静态图片与动态图片（如 GIF）作为水印，可设置不透明度与九宫格位置
"""
import os
import subprocess
from pathlib import Path
from typing import Callable, Optional, List, Tuple

POSITION_OVERLAY = {
    "top_left": "10:10",
    "top": "(main_w-w)/2:10",
    "top_right": "main_w-w-10:10",
    "left": "10:(main_h-h)/2",
    "center": "(main_w-w)/2:(main_h-h)/2",
    "right": "main_w-w-10:(main_h-h)/2",
    "bottom_left": "10:main_h-h-10",
    "bottom": "(main_w-w)/2:main_h-h-10",
    "bottom_right": "main_w-w-10:main_h-h-10",
}


class VideoWatermark:
    """视频水印处理器"""

    def __init__(self, ffmpeg_path: Optional[str] = None):
        if ffmpeg_path is None:
            project_root = Path(__file__).parent.parent.parent
            ffmpeg_path = str(project_root / "tools" / "ffmpeg" / "ffmpeg.exe")
        self.ffmpeg_path = ffmpeg_path
        self.video_exts = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}
        self.image_exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}

    def is_supported_video(self, filepath: str) -> bool:
        return Path(filepath).suffix.lower() in self.video_exts

    def is_supported_watermark(self, filepath: str) -> bool:
        return Path(filepath).suffix.lower() in self.image_exts

    def _is_animated_image(self, filepath: str) -> bool:
        return Path(filepath).suffix.lower() == ".gif"

    def apply_watermark(
        self,
        input_path: str,
        output_path: str,
        watermark_path: str,
        opacity: float = 1.0,
        position: str = "center",
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> Tuple[bool, str]:
        try:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            pos_expr = POSITION_OVERLAY.get(position, POSITION_OVERLAY["center"])
            opacity = max(0.0, min(1.0, opacity))
            wm_input = ["-i", watermark_path]
            if self._is_animated_image(watermark_path):
                wm_input = ["-stream_loop", "-1", "-i", watermark_path]
            filter_complex = (
                f"[1:v]format=rgba,colorchannelmixer=aa={opacity:.4f}[wm];"
                f"[0:v][wm]overlay={pos_expr}[outv]"
            )
            cmd = [
                self.ffmpeg_path, "-i", input_path, *wm_input,
                "-filter_complex", filter_complex, "-map", "[outv]", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p", "-c:a", "copy",
                "-y", output_path,
            ]
            if progress_callback:
                progress_callback(0)
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True, encoding="utf-8", errors="ignore",
            )
            err_lines = []
            for line in process.stderr:
                err_lines.append(line)
            process.wait()
            ok = process.returncode == 0
            if ok and progress_callback:
                progress_callback(100)
            return ok, "".join(err_lines[-15:]).strip() if not ok else ""
        except Exception as e:
            return False, str(e)

    def batch_apply(
        self,
        input_paths: List[str],
        output_dir: str,
        watermark_path: str,
        opacity: float = 1.0,
        position: str = "center",
        progress_callback: Optional[Callable[[int, int, str, float, str], None]] = None,
    ) -> dict:
        results = {}
        total = len(input_paths)
        for idx, inp in enumerate(input_paths, 1):
            name = Path(inp).stem
            ext = Path(inp).suffix or ".mp4"
            out_path = os.path.join(output_dir, f"{name}{ext}")

            def file_progress(pct, i=idx, n=total, fn=name):
                if progress_callback:
                    progress_callback(i, n, fn, pct, "")

            ok, err = self.apply_watermark(
                inp, out_path, watermark_path, opacity, position, file_progress
            )
            if progress_callback:
                progress_callback(idx, total, name, 100.0, err if not ok else "")
            results[inp] = (ok, err)
        return results
