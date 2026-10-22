# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 LKZ666

"""
串口噪声监测 - 噪音监测系统
从CH340串口读取上层/下层分贝数据并实时显示
协议格式: UP:xx.x,DOWN:xx.x\n
波特率: 9600
"""

import sys
import re
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect,
    QPushButton, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, QEasingCurve, QSize
from PyQt5.QtGui import (
    QFont, QColor, QPainter, QLinearGradient, QPainterPath,
    QPen, QFontDatabase, QIcon, QPixmap, QBrush, QPalette
)


# ──────────────────────────── 常量 ────────────────────────────
BAUD_RATE = 9600
SERIAL_TIMEOUT = 0.1
UPDATE_INTERVAL_MS = 100  # UI刷新间隔

# ──────────────────────────── 配色 ────────────────────────────
BG_COLOR = "#e1d5c6"            # 背景米色
CARD_BG = "#ffffff"             # 卡片白色
TITLE_COLOR = "#5a3e28"         # 标题深棕
SUBTITLE_COLOR = "#8c7a6a"      # 副标题浅棕
VALUE_COLOR = "#4a3520"         # 数值深棕
LABEL_COLOR = "#6b5a4a"         # 标签棕色
ACCENT_COLOR = "#8b5e3c"        # 强调色（下划线）
DIFF_LABEL_COLOR = "#a07850"    # 差值标签颜色
BUTTON_BG = "#f5efe8"           # 按钮背景
BUTTON_BORDER = "#c8b8a8"       # 按钮边框
DIVIDER_COLOR = "#e0d5ca"       # 分割线颜色


def find_ch340_port():
    """自动检测CH340串口"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        desc = (port.description or "").upper()
        hwid = (port.hwid or "").upper()
        if "CH340" in desc or "CH341" in desc or "1A86" in hwid:
            return port.device
    # 若未找到CH340，返回第一个可用串口
    if ports:
        return ports[0].device
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━ 数据行组件 ━━━━━━━━━━━━━━━━━━━━━━━━━━
class DataRow(QWidget):
    """单行数据显示：标签 + 数值"""

    def __init__(self, label_text, unit="dB", is_diff=False, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._display_value = 0.0
        self._label_text = label_text
        self._unit = unit
        self._is_diff = is_diff

        self.setFixedHeight(90)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(60, 10, 60, 10)

        # 左侧标签
        self.label = QLabel(label_text)
        label_font = QFont("Microsoft YaHei", 22)
        self.label.setFont(label_font)
        if is_diff:
            self.label.setStyleSheet(f"color: {DIFF_LABEL_COLOR}; background: transparent;")
        else:
            self.label.setStyleSheet(f"color: {LABEL_COLOR}; background: transparent;")
        layout.addWidget(self.label, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        layout.addStretch()

        # 右侧数值
        self.value_label = QLabel("0 dB")
        value_font = QFont("Segoe UI", 24)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet(f"color: {VALUE_COLOR}; background: transparent;")
        layout.addWidget(self.value_label, alignment=Qt.AlignRight | Qt.AlignVCenter)

        # 动画
        self._anim = QPropertyAnimation(self, b"displayValue")
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def get_display_value(self):
        return self._display_value

    def set_display_value(self, v):
        self._display_value = v
        self.value_label.setText(f"{int(round(v))} {self._unit}")
        self.update()

    displayValue = pyqtProperty(float, get_display_value, set_display_value)

    def setValue(self, value):
        value = max(0, min(130, value))
        if abs(value - self._value) < 0.01:
            return
        self._value = value
        self._anim.stop()
        self._anim.setStartValue(self._display_value)
        self._anim.setEndValue(value)
        self._anim.start()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━ 分割线 ━━━━━━━━━━━━━━━━━━━━━━━━━━
class ThinDivider(QWidget):
    """细分割线"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(DIVIDER_COLOR))
        margin = 50
        painter.drawRect(margin, 0, self.width() - 2 * margin, 1)
        painter.end()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━ 主窗口 ━━━━━━━━━━━━━━━━━━━━━━━━━━
class NoiseMonitorWindow(QMainWindow):
    """串口噪声监测 - 主窗口"""

    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.serial_buffer = ""
        self.upstairs_value = 0.0
        self.downstairs_value = 0.0
        self.is_testing = False

        self._init_ui()
        self._init_timers()

    def _init_ui(self):
        self.setWindowTitle("串口噪声监测")
        self.setMinimumSize(900, 650)
        self.resize(1024, 700)

        # 全局背景色
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {BG_COLOR};
            }}
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(50, 35, 50, 35)
        main_layout.setSpacing(0)

        # ── 顶部标题行 ──
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧标题
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(6)

        title_label = QLabel("串口噪声监测")
        title_font = QFont("Microsoft YaHei", 28, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {TITLE_COLOR};")
        title_layout.addWidget(title_label)

        # 标题下划线（实线 + 虚线）
        underline = QWidget()
        underline.setFixedHeight(4)
        underline.setFixedWidth(280)
        title_layout.addWidget(underline)

        header_layout.addWidget(title_widget, alignment=Qt.AlignLeft | Qt.AlignTop)

        header_layout.addStretch()

        # 右侧品牌
        brand_widget = QWidget()
        brand_layout = QHBoxLayout(brand_widget)
        brand_layout.setContentsMargins(0, 5, 0, 0)
        brand_layout.setSpacing(8)

        brand_sub = QLabel("串\n口")
        brand_sub.setFont(QFont("Microsoft YaHei", 9))
        brand_sub.setStyleSheet(f"color: {SUBTITLE_COLOR};")
        brand_sub.setAlignment(Qt.AlignCenter)
        brand_layout.addWidget(brand_sub)

        brand_main = QLabel("Noise Monitor")
        brand_main.setFont(QFont("KaiTi", 22, QFont.Bold))
        brand_main.setStyleSheet(f"color: {TITLE_COLOR};")
        brand_layout.addWidget(brand_main)

        brand_sub2 = QLabel("双\n通道")
        brand_sub2.setFont(QFont("Microsoft YaHei", 9))
        brand_sub2.setStyleSheet(f"color: {SUBTITLE_COLOR};")
        brand_sub2.setAlignment(Qt.AlignCenter)
        brand_layout.addWidget(brand_sub2)

        header_layout.addWidget(brand_widget, alignment=Qt.AlignRight | Qt.AlignTop)

        main_layout.addLayout(header_layout)

        # ── 装饰下划线绘制 ──
        underline_bar = UnderlineWidget()
        underline_bar.setFixedHeight(6)
        underline_bar.setFixedWidth(320)
        main_layout.addWidget(underline_bar, alignment=Qt.AlignLeft)

        main_layout.addSpacing(12)

        # ── 副标题 ──
        subtitle = QLabel("楼下分贝越小　楼板隔声性能越好")
        subtitle.setFont(QFont("Microsoft YaHei", 13))
        subtitle.setStyleSheet(f"color: {SUBTITLE_COLOR};")
        main_layout.addWidget(subtitle, alignment=Qt.AlignLeft)

        main_layout.addSpacing(25)

        # ── 数据卡片 ──
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border-radius: 18px;
                border: 1px solid rgba(200, 190, 175, 0.4);
            }}
        """)

        # 卡片阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 30, 0, 30)
        card_layout.setSpacing(0)

        # 上层分贝
        self.up_row = DataRow("上层分贝")
        card_layout.addWidget(self.up_row)

        card_layout.addWidget(ThinDivider())

        # 下层分贝
        self.down_row = DataRow("下层分贝")
        card_layout.addWidget(self.down_row)

        card_layout.addWidget(ThinDivider())

        # 差值
        self.diff_row = DataRow("差值", is_diff=True)
        card_layout.addWidget(self.diff_row)

        main_layout.addWidget(card, 1)

        main_layout.addSpacing(25)

        # ── 点击测试按钮 ──
        btn_container = QHBoxLayout()
        btn_container.addStretch()

        self.test_btn = QPushButton("  点击测试  👆")
        self.test_btn.setFont(QFont("Microsoft YaHei", 18))
        self.test_btn.setFixedSize(280, 60)
        self.test_btn.setCursor(Qt.PointingHandCursor)
        self._set_btn_idle_style()
        self.test_btn.clicked.connect(self._on_test_click)

        # 按钮阴影
        btn_shadow = QGraphicsDropShadowEffect()
        btn_shadow.setBlurRadius(20)
        btn_shadow.setColor(QColor(0, 0, 0, 20))
        btn_shadow.setOffset(0, 3)
        self.test_btn.setGraphicsEffect(btn_shadow)

        btn_container.addWidget(self.test_btn)
        btn_container.addStretch()

        main_layout.addLayout(btn_container)

        main_layout.addSpacing(10)

        # ── 底部状态 ──
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Microsoft YaHei", 9))
        self.status_label.setStyleSheet(f"color: {SUBTITLE_COLOR};")
        main_layout.addWidget(self.status_label)

    def _set_btn_idle_style(self):
        self.test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_BG};
                color: {TITLE_COLOR};
                border: 1.5px solid {BUTTON_BORDER};
                border-radius: 30px;
                padding: 8px 30px;
                letter-spacing: 4px;
            }}
            QPushButton:hover {{
                background-color: #ece4da;
                border-color: {ACCENT_COLOR};
            }}
            QPushButton:pressed {{
                background-color: #dfd5c8;
            }}
        """)

    def _set_btn_active_style(self):
        self.test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_COLOR};
                color: #ffffff;
                border: 1.5px solid {ACCENT_COLOR};
                border-radius: 30px;
                padding: 8px 30px;
                letter-spacing: 4px;
            }}
            QPushButton:hover {{
                background-color: #7a5030;
            }}
            QPushButton:pressed {{
                background-color: #6a4025;
            }}
        """)

    # ────────── 测试按钮逻辑 ──────────
    def _on_test_click(self):
        if self.is_testing:
            self._stop_testing()
        else:
            self._start_testing()

    def _start_testing(self):
        """开始测试 - 连接串口并读取数据"""
        port = find_ch340_port()
        if port is None:
            self.status_label.setText("❌ 未检测到CH340串口设备，请检查连接")
            self.status_label.setStyleSheet("color: #c0392b;")
            return

        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=BAUD_RATE,
                timeout=SERIAL_TIMEOUT,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self.is_testing = True
            self.test_btn.setText("  停止测试  ⏹")
            self._set_btn_active_style()
            self.status_label.setText(f"✅ 已连接 {port}，正在采集数据...")
            self.status_label.setStyleSheet("color: #27ae60;")
            self.read_timer.start(UPDATE_INTERVAL_MS)

        except serial.SerialException as e:
            self.status_label.setText(f"❌ 串口打开失败: {e}")
            self.status_label.setStyleSheet("color: #c0392b;")

    def _stop_testing(self):
        """停止测试"""
        self.is_testing = False
        self.read_timer.stop()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.serial_port = None
        self.test_btn.setText("  点击测试  👆")
        self._set_btn_idle_style()
        self.status_label.setText("测试已停止")
        self.status_label.setStyleSheet(f"color: {SUBTITLE_COLOR};")

    # ────────── 定时器 ──────────
    def _init_timers(self):
        self.read_timer = QTimer(self)
        self.read_timer.timeout.connect(self._read_serial)
        # 不立即启动，等点击按钮后启动

    # ────────── 串口读取 ──────────
    def _read_serial(self):
        """读取并解析串口数据"""
        if self.serial_port is None or not self.serial_port.is_open:
            return

        try:
            if self.serial_port.in_waiting > 0:
                raw = self.serial_port.read(self.serial_port.in_waiting)
                try:
                    text = raw.decode('ascii', errors='ignore')
                except Exception:
                    return

                self.serial_buffer += text

                while '\n' in self.serial_buffer:
                    line, self.serial_buffer = self.serial_buffer.split('\n', 1)
                    line = line.strip()
                    self._parse_line(line)

                # 防止缓冲区溢出
                if len(self.serial_buffer) > 512:
                    self.serial_buffer = self.serial_buffer[-128:]

        except (serial.SerialException, OSError):
            self._stop_testing()
            self.status_label.setText("⚠️ 串口断开")
            self.status_label.setStyleSheet("color: #e67e22;")

    def _parse_line(self, line):
        """
        解析一行数据
        格式: UP:xx.x,DOWN:xx.x
        """
        match = re.match(r'UP:([\d.]+),DOWN:([\d.]+)', line)
        if match:
            try:
                up_val = float(match.group(1))
                down_val = float(match.group(2))

                self.upstairs_value = max(0, min(130, up_val))
                self.downstairs_value = max(0, min(130, down_val))
                diff_val = abs(self.upstairs_value - self.downstairs_value)

                self.up_row.setValue(self.upstairs_value)
                self.down_row.setValue(self.downstairs_value)
                self.diff_row.setValue(diff_val)

            except ValueError:
                pass

    def closeEvent(self, event):
        """窗口关闭时清理资源"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        event.accept()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━ 装饰下划线 ━━━━━━━━━━━━━━━━━━━━━━━━━━
class UnderlineWidget(QWidget):
    """标题装饰下划线: 实线 + 虚线"""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        y = self.height() // 2

        # 左侧实线 (棕红色)
        solid_len = int(w * 0.35)
        pen = QPen(QColor(ACCENT_COLOR), 3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawLine(0, y, solid_len, y)

        # 右侧虚线
        dash_pen = QPen(QColor(SUBTITLE_COLOR), 1.5)
        dash_pen.setStyle(Qt.DashLine)
        dash_pen.setDashPattern([4, 4])
        painter.setPen(dash_pen)
        painter.drawLine(solid_len + 10, y, w, y)

        painter.end()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━ 入口 ━━━━━━━━━━━━━━━━━━━━━━━━━━
def main():
    app = QApplication(sys.argv)

    # 全局字体
    app.setFont(QFont("Microsoft YaHei", 10))

    window = NoiseMonitorWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
