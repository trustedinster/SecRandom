import os
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QWidget
from loguru import logger

from app.tools.settings_access import readme_settings_async
from app.tools.variable import FONT_APPLY_DELAY


def configure_dpi_scale():
    """在创建QApplication之前配置DPI缩放模式"""
    try:
        dpiScale = readme_settings_async("basic_settings", "dpiScale")
        if dpiScale == "Auto":
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
            os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
            logger.debug("DPI缩放已设置为自动模式")
        else:
            os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
            os.environ["QT_SCALE_FACTOR"] = str(dpiScale)
            logger.debug(f"DPI缩放已设置为{dpiScale}倍")
    except Exception as e:
        logger.warning(f"读取DPI设置失败，使用默认设置: {e}")
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"


def apply_font_settings():
    """应用字体设置 - 优化版本，使用字体管理器异步加载"""
    font_family = readme_settings_async("basic_settings", "font")

    from qfluentwidgets import setFontFamilies

    setFontFamilies([font_family])
    QTimer.singleShot(FONT_APPLY_DELAY, lambda: apply_font_to_application(font_family))


def apply_font_to_application(font_family: str):
    """应用字体设置到整个应用程序，优化版本使用字体管理器

    Args:
        font_family (str): 字体家族名称
    """
    try:
        current_font = QApplication.font()
        app_font = current_font
        app_font.setFamily(font_family)
        widgets_updated = 0
        widgets_skipped = 0
        for widget in QApplication.allWidgets():
            if isinstance(widget, QWidget):
                if update_widget_fonts(widget, app_font, font_family):
                    widgets_updated += 1
                else:
                    widgets_skipped += 1
        logger.debug(
            f"已应用字体: {font_family}, 更新了{widgets_updated}个控件字体, 跳过了{widgets_skipped}个已有相同字体的控件"
        )
    except Exception as e:
        logger.error(f"应用字体失败: {e}")


def update_widget_fonts(widget: QWidget, font, font_family: str) -> bool:
    """更新控件及其子控件的字体，优化版本减少内存占用，特别处理ComboBox等控件

    Args:
        widget: 要更新字体的控件
        font: 要应用的字体
        font_family: 目标字体家族名称

    Returns:
        bool: 是否更新了控件的字体
    """
    if widget is None:
        return False

    try:
        if not hasattr(widget, "font") or not hasattr(widget, "setFont"):
            return False
        current_widget_font = widget.font()
        if current_widget_font.family() == font_family:
            updated = False
        else:
            new_font = font
            new_font.setBold(current_widget_font.bold())
            new_font.setItalic(current_widget_font.italic())
            widget.setFont(new_font)
            updated = True

        if isinstance(widget, QWidget):
            children = widget.children()
            for child in children:
                if isinstance(child, QWidget):
                    child_updated = update_widget_fonts(child, font, font_family)
                    if child_updated:
                        updated = True
        return updated
    except Exception as e:
        logger.exception("更新控件字体时发生异常: {}", e)
        return False
