"""按钮绘制工具函数"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor
from qfluentwidgets.common.color import autoFallbackThemeColor
from qfluentwidgets.common.config import isDarkTheme


def centered_draw_background(button, painter: QPainter, button_size: int):
    """绘制按钮背景，使选中指示条（小蓝条）垂直居中"""
    if button.isSelected:
        painter.setBrush(QColor(255, 255, 255, 42) if isDarkTheme() else Qt.white)
        painter.drawRoundedRect(button.rect(), 5, 5)

        # 绘制指示条（小蓝条），垂直居中
        painter.setBrush(
            autoFallbackThemeColor(button.lightSelectedColor, button.darkSelectedColor)
        )
        indicator_height = 24 if not button.isPressed else 18
        indicator_y = (button_size - indicator_height) // 2
        if button.isPressed:
            indicator_y += 3  # 按下时稍微下移
        painter.drawRoundedRect(0, indicator_y, 4, indicator_height, 2, 2)
    elif button.isPressed or button.isEnter:
        c = 255 if isDarkTheme() else 0
        alpha = 9 if button.isEnter else 6
        painter.setBrush(QColor(c, c, c, alpha))
        painter.drawRoundedRect(button.rect(), 5, 5)
