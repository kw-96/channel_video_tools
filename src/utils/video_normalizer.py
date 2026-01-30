"""
视频规范化核心处理模块
"""
import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional, Dict, List, Tuple


class VideoNormalizer:
    """视频规范化处理器"""

    def __init__(self, ffmpeg_path: str = None, ffprobe_path: str = None):
        if ffmpeg_path is None:
            project_root = Path(__file__).parent.parent.parent
            ffmpeg_path = str(project_root / "tools" / "ffmpeg" / "ffmpeg.exe")
        if ffprobe_path is None:
            ffprobe_path = str(Path(ffmpeg_path).parent / "ffprobe.exe")
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.has_ffprobe = os.path.exists(self.ffprobe_path)
        if not self.has_ffprobe:
            print("警告: 未找到 ffprobe，将无法显示详细进度信息")
        self.supported_formats = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}

    def get_video_info(self, video_path: str) -> Optional[Dict]:
        """获取视频信息（宽高、时长）"""
        if not self.has_ffprobe:
            return None
        try:
            cmd = [self.ffprobe_path, "-v", "quiet", "-print_format", "json", "-show_streams", video_path]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            if result.returncode == 0:
                data = json.loads(result.stdout)
                video_stream = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
                if video_stream:
                    return {
                        "width": int(video_stream.get("width", 0)),
                        "height": int(video_stream.get("height", 0)),
                        "duration": float(video_stream.get("duration", 0)),
                    }
        except Exception as e:
            print(f"获取视频信息失败: {e}")
        return None

    def check_video_size(self, video_path: str, target_width: int, target_height: int) -> bool:
        """检查视频尺寸是否符合目标尺寸"""
        info = self.get_video_info(video_path)
        return info and info["width"] == target_width and info["height"] == target_height

    def _parse_ffmpeg_progress(self, line: str, duration: float) -> Optional[float]:
        if "time=" not in line:
            return None
        try:
            time_str = line.split("time=")[1].split()[0]
            h, m, s = time_str.split(":")
            t = int(h) * 3600 + int(m) * 60 + float(s)
            return min(100, (t / duration) * 100)
        except Exception:
            return None

    def _run_with_progress(
        self, cmd: List[str], duration: float, progress_callback: Callable[[float], None]
    ) -> Tuple[bool, str]:
        progress_callback(0)
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, encoding="utf-8", errors="ignore"
        )
        error_lines = []
        for line in process.stderr:
            error_lines.append(line)
            p = self._parse_ffmpeg_progress(line, duration)
            if p is not None:
                progress_callback(p)
        process.wait()
        ok = process.returncode == 0
        if ok:
            progress_callback(100)
        return ok, "".join(error_lines[-10:]).strip() if not ok else ""

    def _build_filter(self, target_width: int, target_height: int, pad_color: str) -> str:
        return f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:{pad_color}"

    def normalize_video(
        self,
        input_path: str,
        output_path: str,
        target_width: int,
        target_height: int,
        pad_color: str = "black",
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> Tuple[bool, str, str]:
        """规范化单个视频，返回（成功, 操作类型, 错误信息）"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            if self.check_video_size(input_path, target_width, target_height):
                shutil.copy2(input_path, output_path)
                if progress_callback:
                    progress_callback(100)
                return True, "copied", ""
            filt = self._build_filter(target_width, target_height, pad_color)
            cmd = [
                self.ffmpeg_path, "-noautorotate", "-i", input_path,
                "-vf", filt, "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "fast",
                "-vsync", "cfr", "-r", "30", "-c:a", "aac", "-b:a", "128k", "-y", output_path,
            ]
            if progress_callback and self.has_ffprobe:
                info = self.get_video_info(input_path)
                if info and info.get("duration", 0) > 0:
                    ok, err = self._run_with_progress(cmd, info["duration"], progress_callback)
                    return ok, "processed", err
            if progress_callback:
                progress_callback(0)
            result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="ignore")
            ok = result.returncode == 0
            if ok and progress_callback:
                progress_callback(100)
            err = "" if ok else (result.stderr or "ffmpeg返回非零")
            return ok, "processed", err
        except Exception as e:
            return False, "failed", str(e)

    def batch_normalize(
        self,
        input_paths: List[str],
        output_dir: str,
        target_width: int,
        target_height: int,
        pad_color: str = "black",
        progress_callback: Optional[Callable[[int, int, str, float, str, str], None]] = None,
    ) -> Dict[str, Tuple[bool, str, str]]:
        """批量规范化视频"""
        results = {}
        total = len(input_paths)
        for idx, inp in enumerate(input_paths, 1):
            name = os.path.basename(inp)
            out_path = os.path.join(output_dir, name)

            def file_progress(pct, i=idx, n=total, fn=name):
                if progress_callback:
                    progress_callback(i, n, fn, pct, "", "")

            ok, action, err = self.normalize_video(
                inp, out_path, target_width, target_height, pad_color, file_progress
            )
            if progress_callback:
                progress_callback(idx, total, name, 100, action, err)
            results[inp] = (ok, action, err)
        return results

    def is_supported_format(self, filepath: str) -> bool:
        return Path(filepath).suffix.lower() in self.supported_formats
