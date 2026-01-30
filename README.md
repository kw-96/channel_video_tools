# 渠道视频批量处理工具

本工具为**渠道视频批量处理**独立项目，采用 **Tauri 2 + Vue 3 + Python** 架构：前端 Vue 界面、Tauri 桌面壳、Python 提供视频规范/水印/合并及主题设置 API。

## 功能

- **视频规范**：批量将视频统一为目标分辨率（横版/竖版），保持宽高比并填充黑边。
- **视频水印**：批量为视频添加静态或动态水印，可设置不透明度与九宫格位置。
- **视频合并**：批量为视频添加片头或片尾，主体与插入视频尺寸需一致。
- **主题切换**：深色/浅色主题，设置会持久化保存。

## 环境要求

- **Node.js** 18+（前端与 Tauri CLI）
- **Rust**（Tauri 2 构建，安装见 [rustup](https://rustup.rs/)）
- **Windows 用户（Tauri 构建）**：二选一。
  - **有管理员权限**：安装 [Visual Studio 生成工具](https://visualstudio.microsoft.com/zh-hans/visual-cpp-build-tools/)，勾选「使用 C++ 的桌面开发」。
  - **无管理员权限**：使用 GNU 工具链，见下方「无管理员权限时（GNU 工具链）」。
- **Python** 3.8+（后端 API）
- **FFmpeg**（含 ffprobe）：请将 `ffmpeg.exe`、`ffprobe.exe` 等放入 `tools/ffmpeg/` 目录，或确保系统 PATH 中已安装；程序优先使用 `tools/ffmpeg/` 下的可执行文件。

### 无管理员权限时（GNU 工具链）

无需安装 Visual Studio，用 MinGW 替代 MSVC 即可编译 Tauri。

1. **下载 MinGW-w64 便携版（免安装）**
   - 打开 [WinLibs](https://winlibs.com/)，选 **Release versions**。
   - 下载 64 位、UCRT 运行时、不带 LLVM 的 zip（例如：GCC 13.x + MinGW-w64 11.x，文件名含 `ucrt`、`x86_64`）。
   - 解压到当前用户可写目录，例如 `C:\Users\你的用户名\mingw64`（或项目下的 `tools\mingw64`）。记住解压后的 **bin** 路径（如 `C:\Users\你的用户名\mingw64\bin`）。

2. **将 MinGW 加入用户 PATH**
   - 按 Win+R，输入 `sysdm.cpl` 回车 →「高级」→「环境变量」。
   - 在「用户变量」里选中 `Path` →「编辑」→「新建」，填入上一步的 **bin** 路径 → 确定保存。
   - **重新打开终端**（或重启 Cursor），使 PATH 生效。

3. **让 Rust 使用 GNU 工具链**
   - 在终端执行：
   ```bash
   rustup default stable-x86_64-pc-windows-gnu
   ```
   - 若未安装该目标，rustup 会先下载。

4. **验证**
   - 执行 `gcc --version` 应能看到 GCC 版本；再执行 `npm run tauri dev` 进行构建。

## 快速开始

### 1. 安装依赖

**前端（项目根目录）：**

```bash
npm install
cd frontend
npm install
cd ..
```

**Python 后端：**

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r api/requirements.txt
```

### 2. 开发运行

Tauri 启动时会自动在后台启动 Python API（`api/main.py`），无需单独开终端。

在项目根目录执行：

```bash
npm run tauri dev
```

或使用快捷脚本：

```bash
npm run dev:tauri
```

将依次：启动 Vue 开发服务器、编译 Tauri、打开桌面窗口并拉起 Python API（端口 8765）。前端通过 `http://127.0.0.1:8765` 调用后端。

若需单独调试 API，可先运行：

```bash
python api/main.py
```

再在浏览器访问 `http://127.0.0.1:8765/docs` 查看接口文档。

### 3. 打包为 exe

在项目根目录执行：

```bash
npm run build
npm run tauri build
```

或使用快捷脚本：`npm run build:tauri`（需先执行 `npm run build` 生成前端产物）。

产物在 `src-tauri/target/release/` 下（或 `target/release/bundle/msi` 等安装包）。打包时 Python 逻辑通过本地 API 调用，需保证运行环境中已安装 Python 并安装 `api/requirements.txt` 与项目 `requirements.txt`；后续可将 Python 打成 sidecar 以一体化分发。

## 目录结构

```
channel_video_tools/
  package.json           # 根脚本：tauri、dev、build、api
  frontend/              # Vue 3 前端
    src/
      views/             # 视频规范、水印、合并页
      api.js             # 后端 API 封装
      App.vue
    index.html
    vite.config.js
  src-tauri/             # Tauri 2 壳
    src/
      lib.rs             # 启动 Python API、运行 Tauri
      main.rs
    tauri.conf.json
    capabilities/
  api/                   # Python FastAPI 后端
    main.py              # 主题、规范、水印、合并接口
    requirements.txt
  src/                   # Python 核心（沿用）
    config/              # 主题设置
    utils/               # 视频规范、水印、合并
    gui/                 # 原 CustomTkinter 界面（可选）
  main.py                # 原 Python 入口（可选，仍可 python main.py）
  config/
  tools/ffmpeg/           # 放置 ffmpeg.exe、ffprobe.exe（见该目录 README）
```

## 可选：仅用 Python 原界面

若不想使用 Tauri + Vue，可继续使用原 CustomTkinter 界面：

```bash
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

开发模式下自动重启界面：

```bash
pip install -r requirements-dev.txt
python run_dev.py
```

## 与 FFmpeg 的关系

- 请将 FFmpeg 可执行文件（`ffmpeg.exe`、`ffprobe.exe` 等）放入 `tools/ffmpeg/` 目录，详见该目录下 `README.md`。Python 后端优先使用该目录下的可执行文件。
- 若系统 PATH 中已安装 FFmpeg，后端会回退尝试系统路径，此时 `tools/ffmpeg/` 可留空。
