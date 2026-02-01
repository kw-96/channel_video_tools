use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};

/// 视频文件扩展名（小写）
const VIDEO_EXT: &[&str] = &["mp4", "mkv", "avi", "mov", "wmv", "flv", "webm"];

/// 列出目录下所有视频文件路径（仅当前目录，不递归）
#[tauri::command]
fn list_video_files_in_dir(dir: String) -> Result<Vec<String>, String> {
    let path = Path::new(&dir);
    if !path.is_dir() {
        return Err("不是有效目录".to_string());
    }
    let mut out = Vec::new();
    for e in std::fs::read_dir(path).map_err(|e| e.to_string())? {
        let e = e.map_err(|e| e.to_string())?;
        let p = e.path();
        if p.is_file() {
            if let Some(ext) = p.extension() {
                let ext = ext.to_string_lossy().to_lowercase();
                if VIDEO_EXT.contains(&ext.as_str()) {
                    if let Ok(s) = p.into_os_string().into_string() {
                        out.push(s);
                    }
                }
            }
        }
    }
    out.sort();
    Ok(out)
}

fn project_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).parent().unwrap().to_path_buf()
}

fn start_python_api() -> Option<Child> {
    let root = project_root();
    let api_main = root.join("api").join("main.py");
    if !api_main.exists() {
        eprintln!("Python API not found: {:?}", api_main);
        return None;
    }
    let python = which_python(&root);
    let child = Command::new(&python)
        .arg(api_main)
        .current_dir(root)
        .stdout(Stdio::null())
        .stderr(Stdio::piped())
        .spawn()
        .ok()?;
    Some(child)
}

/// 优先使用项目根目录下的 venv，其次环境变量 PYTHON，最后系统 python
fn which_python(root: &Path) -> PathBuf {
    if let Ok(p) = std::env::var("PYTHON") {
        return PathBuf::from(p);
    }
    let venv_python = if cfg!(windows) {
        root.join("venv").join("Scripts").join("python.exe")
    } else {
        root.join("venv").join("bin").join("python")
    };
    if venv_python.exists() {
        return venv_python;
    }
    if cfg!(windows) {
        PathBuf::from("python")
    } else {
        PathBuf::from("python3")
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let _child = start_python_api();
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![list_video_files_in_dir])
        .setup(|_app| {
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
