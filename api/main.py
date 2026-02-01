"""
渠道视频批量处理 - FastAPI 后端
供 Tauri + Vue 前端调用：视频规范、水印、合并及主题设置
"""
import json
import sys
import threading
from pathlib import Path
from queue import Empty, Queue

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# 后端端口，与前端 / Tauri 约定一致
API_PORT = 8765


def get_config_dir() -> Path:
    return _root / "config"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # 关闭时无需特别清理


app = FastAPI(title="渠道视频批量处理 API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 主题 ----------
class ThemeResponse(BaseModel):
    mode: str


class ThemeSetBody(BaseModel):
    mode: str


@app.get("/api/theme", response_model=ThemeResponse)
def get_theme():
    try:
        from config.settings import ThemeSettingsManager
        mgr = ThemeSettingsManager(str(get_config_dir()))
        return ThemeResponse(mode=mgr.get_theme_setting())
    except Exception as e:
        return ThemeResponse(mode="dark")


@app.post("/api/theme", response_model=ThemeResponse)
def set_theme(body: ThemeSetBody):
    try:
        from config.settings import ThemeSettingsManager
        mgr = ThemeSettingsManager(str(get_config_dir()))
        if body.mode not in ("dark", "light"):
            body.mode = "dark"
        mgr.set_theme_setting(body.mode)
        return ThemeResponse(mode=body.mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- 视频规范 ----------
class NormalizeBody(BaseModel):
    input_paths: list[str]
    output_dir: str
    target_width: int = 1920
    target_height: int = 1080
    pad_color: str = "black"


class NormalizeResult(BaseModel):
    ok: bool
    results: dict[str, list]  # path -> [ok, action, err]


@app.post("/api/normalize", response_model=NormalizeResult)
def normalize_videos(body: NormalizeBody):
    try:
        from utils.video_normalizer import VideoNormalizer
        normalizer = VideoNormalizer()
        results = normalizer.batch_normalize(
            body.input_paths,
            body.output_dir,
            body.target_width,
            body.target_height,
            body.pad_color,
        )
        out = {}
        for path, (ok, action, err) in results.items():
            out[path] = [ok, action, err or ""]
        return NormalizeResult(ok=all(r[0] for r in results.values()), results=out)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/normalize/stream")
def normalize_videos_stream(body: NormalizeBody):
    """流式返回：实时日志与进度，最后返回 done 事件"""
    queue = Queue()

    def progress_cb(idx: int, total: int, name: str, pct: float, action: str, err: str):
        if pct < 100:
            queue.put(("log", f"正在处理 {idx}/{total}: {name}"))
        else:
            if action:
                if err:
                    queue.put(("log", f"失败 [{idx}/{total}]: {name} - {err}"))
                else:
                    queue.put(("log", f"完成 [{idx}/{total}]: {name}"))
        progress_pct = ((idx - 1) * 100 + min(pct, 100)) / total if total else 0
        queue.put(("progress", round(progress_pct, 1)))

    def run():
        try:
            from utils.video_normalizer import VideoNormalizer
            normalizer = VideoNormalizer()
            results = normalizer.batch_normalize(
                body.input_paths,
                body.output_dir,
                body.target_width,
                body.target_height,
                body.pad_color,
                progress_callback=progress_cb,
            )
            ok_count = sum(1 for r in results.values() if r[0])
            fail_count = len(results) - ok_count
            queue.put(("done", {"ok": ok_count == len(results), "ok_count": ok_count, "fail_count": fail_count, "results": {k: list(v) for k, v in results.items()}}))
        except Exception as e:
            queue.put(("log", f"错误: {e}"))
            queue.put(("done", {"ok": False, "ok_count": 0, "fail_count": len(body.input_paths), "results": {}, "error": str(e)}))

    threading.Thread(target=run, daemon=True).start()

    def gen():
        while True:
            try:
                ev = queue.get(timeout=300)
            except Empty:
                yield f"data: {json.dumps({'type': 'done', 'ok': False, 'error': '超时'})}\n\n"
                break
            if ev[0] == "log":
                yield f"data: {json.dumps({'type': 'log', 'msg': ev[1]})}\n\n"
            elif ev[0] == "progress":
                yield f"data: {json.dumps({'type': 'progress', 'value': ev[1]})}\n\n"
            elif ev[0] == "done":
                yield f"data: {json.dumps({'type': 'done', **ev[1]})}\n\n"
                break

    return StreamingResponse(gen(), media_type="text/event-stream")


# ---------- 视频水印 ----------
class WatermarkBody(BaseModel):
    input_paths: list[str]
    output_dir: str
    watermark_path: str
    opacity: float = 1.0
    position: str = "center"


class WatermarkResult(BaseModel):
    ok: bool
    results: dict[str, list]


@app.post("/api/watermark", response_model=WatermarkResult)
def watermark_videos(body: WatermarkBody):
    try:
        from utils.video_watermark import VideoWatermark
        import os
        wm = VideoWatermark()
        results = {}
        for inp in body.input_paths:
            if not wm.is_supported_video(inp):
                results[inp] = [False, "unsupported", ""]
                continue
            name = os.path.basename(inp)
            out_path = os.path.join(body.output_dir, name)
            ok, err = wm.apply_watermark(
                inp, out_path, body.watermark_path,
                opacity=body.opacity, position=body.position,
            )
            results[inp] = [ok, "processed", err or ""]
        return WatermarkResult(ok=all(r[0] for r in results.values()), results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/watermark/stream")
def watermark_videos_stream(body: WatermarkBody):
    """流式返回：实时日志与进度，最后返回 done 事件"""
    import os
    queue = Queue()

    def run():
        try:
            from utils.video_watermark import VideoWatermark
            wm = VideoWatermark()
            results = {}
            total = len(body.input_paths)
            for idx, inp in enumerate(body.input_paths, 1):
                if not wm.is_supported_video(inp):
                    results[inp] = (False, "unsupported")
                    queue.put(("log", f"跳过 [{idx}/{total}]: {os.path.basename(inp)} 格式不支持"))
                    queue.put(("progress", round(idx * 100 / total, 1)))
                    continue
                name = os.path.basename(inp)
                out_path = os.path.join(body.output_dir, name)
                queue.put(("log", f"正在处理 {idx}/{total}: {name}"))

                def file_progress(pct, i=idx, n=total):
                    progress_pct = ((i - 1) * 100 + min(pct, 100)) / n if n else 0
                    queue.put(("progress", round(progress_pct, 1)))

                ok, err = wm.apply_watermark(
                    inp, out_path, body.watermark_path,
                    opacity=body.opacity, position=body.position,
                    progress_callback=file_progress,
                )
                if err:
                    queue.put(("log", f"失败 [{idx}/{total}]: {name} - {err}"))
                else:
                    queue.put(("log", f"完成 [{idx}/{total}]: {name}"))
                queue.put(("progress", round(idx * 100 / total, 1)))
                results[inp] = (ok, err or "")
            ok_count = sum(1 for r in results.values() if r[0])
            fail_count = len(results) - ok_count
            queue.put(("done", {"ok": fail_count == 0, "ok_count": ok_count, "fail_count": fail_count, "results": {k: [v[0], "processed", v[1] or ""] for k, v in results.items()}}))
        except Exception as e:
            queue.put(("log", f"错误: {e}"))
            queue.put(("done", {"ok": False, "ok_count": 0, "fail_count": len(body.input_paths), "results": {}, "error": str(e)}))

    threading.Thread(target=run, daemon=True).start()

    def gen():
        while True:
            try:
                ev = queue.get(timeout=300)
            except Empty:
                yield f"data: {json.dumps({'type': 'done', 'ok': False, 'error': '超时'})}\n\n"
                break
            if ev[0] == "log":
                yield f"data: {json.dumps({'type': 'log', 'msg': ev[1]})}\n\n"
            elif ev[0] == "progress":
                yield f"data: {json.dumps({'type': 'progress', 'value': ev[1]})}\n\n"
            elif ev[0] == "done":
                yield f"data: {json.dumps({'type': 'done', **ev[1]})}\n\n"
                break

    return StreamingResponse(gen(), media_type="text/event-stream")


# ---------- 视频合并 ----------
class MergeBody(BaseModel):
    main_video: str
    insert_video: str
    output_path: str
    insert_position: str = "head"


class MergeResult(BaseModel):
    ok: bool
    message: str


@app.post("/api/merge", response_model=MergeResult)
def merge_videos(body: MergeBody):
    try:
        from utils.video_merger import VideoMerger
        merger = VideoMerger()
        ok, msg = merger.merge_videos(
            body.main_video,
            body.insert_video,
            body.output_path,
            insert_position=body.insert_position,
        )
        return MergeResult(ok=ok, message=msg or "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=API_PORT)
