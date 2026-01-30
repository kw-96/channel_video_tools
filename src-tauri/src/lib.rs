use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use tauri::Manager;

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
    let python = which_python();
    let child = Command::new(python)
        .arg(api_main)
        .current_dir(root)
        .stdout(Stdio::null())
        .stderr(Stdio::piped())
        .spawn()
        .ok()?;
    Some(child)
}

fn which_python() -> String {
    if std::env::var("PYTHON").is_ok() {
        return std::env::var("PYTHON").unwrap();
    }
    if cfg!(windows) {
        "python".to_string()
    } else {
        "python3".to_string()
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let _child = start_python_api();
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|_app| {
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
