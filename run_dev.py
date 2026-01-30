"""
开发模式入口：监听代码变更后自动重启应用，便于界面与逻辑修改后即时查看效果。
用法：在本项目根目录执行 python run_dev.py
"""
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:
    print("开发模式需要安装 watchdog，请执行：pip install watchdog")
    sys.exit(1)

# 项目根目录
ROOT = Path(__file__).resolve().parent
# 监听范围：仅 .py 文件，排除 venv、__pycache__、.git
WATCH_DIRS = [ROOT, ROOT / "src"]
DEBOUNCE_SEC = 0.8


class RestartHandler(FileSystemEventHandler):
    """文件变更时请求重启（带防抖）"""

    def __init__(self, on_restart):
        super().__init__()
        self._on_restart = on_restart
        self._timer = None
        self._lock = threading.Lock()

    def _schedule_restart(self):
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(DEBOUNCE_SEC, self._do_restart)
            self._timer.daemon = True
            self._timer.start()

    def _do_restart(self):
        with self._lock:
            self._timer = None
        self._on_restart()

    def _is_py(self, path: str) -> bool:
        p = Path(path)
        if p.suffix != ".py":
            return False
        try:
            r = p.resolve().relative_to(ROOT)
        except ValueError:
            return False
        parts = r.parts
        if "venv" in parts or "__pycache__" in parts or ".git" in parts:
            return False
        return True

    def on_modified(self, event):
        if event.is_directory:
            return
        if self._is_py(event.src_path):
            self._schedule_restart()

    def on_moved(self, event):
        if event.is_directory:
            return
        if self._is_py(event.dest_path) or self._is_py(event.src_path):
            self._schedule_restart()


def main():
    process = [None]  # 用列表以便在闭包中赋值
    restart_requested = threading.Event()

    def request_restart():
        restart_requested.set()
        if process[0] and process[0].poll() is None:
            process[0].terminate()

    handler = RestartHandler(on_restart=request_restart)
    observer = Observer()
    for d in WATCH_DIRS:
        if d.exists():
            observer.schedule(handler, str(d), recursive=True)
    observer.start()
    try:
        while True:
            restart_requested.clear()
            cmd = [sys.executable, str(ROOT / "main.py")]
            env = os.environ.copy()
            env["CHANNEL_VIDEO_DEV"] = "1"
            process[0] = subprocess.Popen(
                cmd,
                cwd=str(ROOT),
                env=env,
                stdout=sys.stdout,
                stderr=sys.stderr,
                stdin=sys.stdin,
            )
            process[0].wait()
            if not restart_requested.is_set():
                break
            print("\n[run_dev] 检测到代码变更，正在重启...\n")
    except KeyboardInterrupt:
        if process[0] and process[0].poll() is None:
            process[0].terminate()
            process[0].wait()
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
