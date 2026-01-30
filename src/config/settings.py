"""
主题设置管理 - 仅负责界面主题的读取与保存
"""
import json
from pathlib import Path
from typing import Any, Dict


class ThemeSettingsManager:
    """主题设置管理器"""

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.config_dir / "system_settings.json"
        self.settings: Dict[str, Any] = {"theme": {"mode": "dark", "description": "界面主题模式"}}
        self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        """从文件加载设置"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if "theme" in loaded:
                        self.settings["theme"] = loaded["theme"]
            except (json.JSONDecodeError, OSError):
                pass
        return self.settings

    def save_settings(self) -> bool:
        """保存设置到文件"""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except OSError:
            return False

    def get_theme_setting(self) -> str:
        """获取主题模式"""
        return self.settings.get("theme", {}).get("mode", "dark")

    def set_theme_setting(self, mode: str) -> bool:
        """设置主题模式"""
        if "theme" not in self.settings:
            self.settings["theme"] = {}
        self.settings["theme"]["mode"] = mode
        return self.save_settings()
