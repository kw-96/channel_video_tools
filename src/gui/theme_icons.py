"""
主题切换图标 - 使用 Lucide 图标库（通过 iconipy）生成太阳/月亮图标
深色模式显示太阳图标（点击切换至浅色），浅色模式显示月亮图标（点击切换至深色）
"""
from typing import Optional, Tuple

import customtkinter as ctk


def _make_theme_ctk_images(
    size: Tuple[int, int] = (24, 24),
    light_color: Tuple[int, int, int, int] = (80, 80, 80, 255),
    dark_color: Tuple[int, int, int, int] = (200, 200, 200, 255),
) -> Tuple[Optional[ctk.CTkImage], Optional[ctk.CTkImage]]:
    """
    使用 iconipy + Lucide 生成太阳、月亮 PIL 图并封装为 CTkImage。
    返回 (sun_ctk_image, moon_ctk_image)，任一方失败则返回 (None, None)。
    """
    try:
        from PIL import Image
        from iconipy import IconFactory
    except ImportError:
        return None, None
    try:
        factory_light = IconFactory(
            icon_set="lucide",
            icon_size=size,
            font_size=max(size) - 4,
            font_color=light_color,
        )
        factory_dark = IconFactory(
            icon_set="lucide",
            icon_size=size,
            font_size=max(size) - 4,
            font_color=dark_color,
        )
        sun_light = factory_light.asPil("sun")
        sun_dark = factory_dark.asPil("sun")
        moon_light = factory_light.asPil("moon")
        moon_dark = factory_dark.asPil("moon")
        sun_ctk = ctk.CTkImage(
            light_image=sun_light,
            dark_image=sun_dark,
            size=size,
        )
        moon_ctk = ctk.CTkImage(
            light_image=moon_light,
            dark_image=moon_dark,
            size=size,
        )
        return sun_ctk, moon_ctk
    except Exception:
        return None, None


def get_theme_button_images(
    size: Tuple[int, int] = (24, 24),
) -> Tuple[Optional[ctk.CTkImage], Optional[ctk.CTkImage]]:
    """
    获取主题切换按钮用的太阳、月亮 CTkImage。
    深色界面时显示太阳（切到浅色），浅色界面时显示月亮（切到深色）。
    """
    return _make_theme_ctk_images(size=size)
