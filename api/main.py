"""
渠道视频批量处理 - FastAPI 后端
供 Tauri + Vue 前端调用：视频规范、水印、合并及主题设置
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
if str(_root / "src") not in sys.path:
    sys.path.insert(0, str(_root / "src"))

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
