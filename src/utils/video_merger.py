"""
视频合并核心处理模块
支持将片头或片尾插入到主体视频中
"""
import json
import os
import subprocess
from pathlib import Path
from typing import Callable, Optional, List, Tuple


class VideoMerger:
    """视频合并处理器"""

    def __init__(self, ffmpeg_path: str = None):
        if ffmpeg_path is None:
            project_root = Path(__file__).parent.parent.parent
            ffmpeg_path = str(project_root / "tools" / "ffmpeg" / "ffmpeg.exe")
        self.ffmpeg_path = ffmpeg_path
        self.supported_formats = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}

    def is_supported_format(self, filepath: str) -> bool:
        return Path(filepath).suffix.lower() in self.supported_formats

    def _get_video_size(self, video_path: str) -> Tuple[int, int]:
        ffprobe_path = str(Path(self.ffmpeg_path).parent / "ffprobe.exe")
        if not os.path.exists(ffprobe_path):
            return 1920, 1080
        try:
            cmd = [ffprobe_path, "-v", "quiet", "-print_format", "json", "-show_streams", video_path]
            out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            if out.returncode != 0 or not out.stdout:
                return 1920, 1080
            data = json.loads(out.stdout)
            for s in data.get("streams", []):
                if s.get("codec_type") == "video":
                    w, h = int(s.get("width", 0)), int(s.get("height", 0))
                    if w > 0 and h > 0:
                        return w, h
            return 1920, 1080
        except Exception:
            return 1920, 1080

    def merge_videos(
        self,
        main_video: str,
        insert_video: str,
        output_path: str,
        insert_position: str = "head",
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> Tuple[bool, str]:
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            video_list = [insert_video, main_video] if insert_position == "head" else [main_video, insert_video]
            target_w, target_h = self._get_video_size(main_video)
            insert_w, insert_h = self._get_video_size(insert_video)
            if (target_w, target_h) != (insert_w, insert_h):
                return False, (
                    f"插入视频与主体视频尺寸不一致，请先调整尺寸后再合并。"
                    f"主体：{target_w}x{target_h}，插入：{insert_w}x{insert_h}。"
                )
            input_args = []
            filter_parts = []
            for idx, video in enumerate(video_list):
                input_args.extend(["-i", video])
                filter_parts.append(
                    f"[{idx}:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
                    f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps=30,"
                    f"format=yuv420p[v{idx}]"
                )
                filter_parts.append(f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=stereo[a{idx}]")
            v_in = "".join([f"[v{i}]" for i in range(len(video_list))])
            a_in = "".join([f"[a{i}]" for i in range(len(video_list))])
            n = len(video_list)
            filter_complex = ";".join(filter_parts) + f";{v_in}concat=n={n}:v=1[outv];{a_in}concat=n={n}:v=0:a=1[outa]"
            cmd = [
                self.ffmpeg_path, *input_args, "-filter_complex", filter_complex,
                "-map", "[outv]", "-map", "[outa]", "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p", "-y", output_path,
            ]
            if progress_callback:
                progress_callback(0)
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True, encoding="utf-8", errors="ignore",
            )
            err_out = []
            for line in process.stderr:
                err_out.append(line)
            process.wait()
            ok = process.returncode == 0
            if ok and progress_callback:
                progress_callback(100)
            return (True, "") if ok else (False, "".join(err_out[-20:]).strip())
        except Exception as e:
            return False, str(e)

    def batch_merge(
        self,
        main_videos: List[str],
        insert_video: str,
        output_dir: str,
        insert_position: str = "head",
        progress_callback: Optional[Callable[[int, int, str, float, str], None]] = None,
    ) -> dict:
        results = {}
        total = len(main_videos)
        num_digits = max(2, len(str(total)))
        for idx, main_video in enumerate(main_videos, 1):
            ext = Path(main_video).suffix or ".mp4"
            output_path = os.path.join(output_dir, f"{idx:0{num_digits}d}_merged{ext}")
            filename = Path(main_video).stem

            def file_progress(percent):
                if progress_callback:
                    progress_callback(idx, total, filename, percent, "")

            ok, err = self.merge_videos(
                main_video, insert_video, output_path, insert_position, file_progress
            )
            if progress_callback:
                progress_callback(idx, total, filename, 100, err if not ok else "")
            results[main_video] = (ok, err)
        return results
