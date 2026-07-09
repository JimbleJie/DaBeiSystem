import ctypes
import os
import platform
import sys
import threading
from pathlib import Path
from typing import Any

from .storage import ROOT


DEFAULT_PRINTER_PID = 672
DEFAULT_PRINTER_VID = 10473
DEFAULT_LABEL_WIDTH_MM = 30
DEFAULT_LABEL_HEIGHT_MM = 40
DEFAULT_DOTS_PER_MM = 8
DEFAULT_QR_CELL_WIDTH = 6

ERROR_MESSAGES = {
    -1: "打印异常",
    0: "成功",
    1: "未连接打印机",
    2: "打印机忙",
    3: "文件不存在",
}

_sdk_lock = threading.Lock()
_sdk: "DDPrintSdk | None" = None


class PrinterUnavailable(Exception):
    pass


class PrinterError(Exception):
    pass


def print_labels(labels: list[dict[str, Any]], copies: int = 1) -> dict[str, Any]:
    if not labels:
        raise PrinterError("没有可打印的标签")
    if copies <= 0:
        raise PrinterError("打印份数必须大于 0")

    sdk = get_sdk()
    printed = 0
    with _sdk_lock:
        sdk.connect()
        for label in labels:
            sdk.print_qr_name_label(
                label_code=str(label.get("labelCode") or ""),
                product_name=str(label.get("productName") or ""),
                copies=copies,
            )
            printed += 1

    return {
        "printed": printed,
        "copies": copies,
        "layout": get_label_layout(),
    }


def get_printer_status() -> dict[str, Any]:
    enabled = is_printing_enabled()
    available, reason = get_availability()
    return {
        "enabled": enabled,
        "available": available,
        "reason": reason,
        "platform": sys.platform,
        "architecture": platform.architecture()[0],
        "sdkDir": str(get_sdk_dir()),
        "dllPath": str(get_dll_path()),
        "pid": get_int_env("PRINT_PRINTER_PID", DEFAULT_PRINTER_PID),
        "vid": get_int_env("PRINT_PRINTER_VID", DEFAULT_PRINTER_VID),
        "layout": get_label_layout(),
    }


def get_sdk() -> "DDPrintSdk":
    global _sdk
    if _sdk is None:
        _sdk = DDPrintSdk(get_dll_path())
    return _sdk


def get_availability() -> tuple[bool, str | None]:
    if not is_printing_enabled():
        return False, "打印功能未启用"
    if os.name != "nt":
        return False, "当前不是 Windows 系统，无法加载 DDPrintSDK.dll"
    if platform.architecture()[0] != "32bit":
        return False, "DDPrintSDK.dll 是 32 位 DLL，需要 32 位 Python 或 x86 打印适配层"
    if not get_dll_path().exists():
        return False, f"未找到 SDK 文件：{get_dll_path()}"
    return True, None


def is_printing_enabled() -> bool:
    return os.getenv("PRINT_SDK_ENABLED", "1") != "0"


def get_sdk_dir() -> Path:
    return Path(os.getenv("PRINT_SDK_DIR", ROOT / "printer-sdk" / "printSDK"))


def get_dll_path() -> Path:
    return get_sdk_dir() / "DDPrintSDK.dll"


def get_label_layout() -> dict[str, int]:
    width_mm = get_int_env("PRINT_LABEL_WIDTH_MM", DEFAULT_LABEL_WIDTH_MM)
    height_mm = get_int_env("PRINT_LABEL_HEIGHT_MM", DEFAULT_LABEL_HEIGHT_MM)
    dots_per_mm = get_int_env("PRINT_LABEL_DOTS_PER_MM", DEFAULT_DOTS_PER_MM)
    qr_cell_width = get_int_env("PRINT_LABEL_QR_CELL_WIDTH", DEFAULT_QR_CELL_WIDTH)
    width_dots = width_mm * dots_per_mm

    qr_modules = get_int_env("PRINT_LABEL_QR_MODULES", 25)
    qr_size = qr_modules * qr_cell_width
    qr_x = get_int_env("PRINT_LABEL_QR_X", max((width_dots - qr_size) // 2, 0))

    return {
        "widthMm": width_mm,
        "heightMm": height_mm,
        "dotsPerMm": dots_per_mm,
        "qrX": qr_x,
        "qrY": get_int_env("PRINT_LABEL_QR_Y", 18),
        "qrCellWidth": qr_cell_width,
        "textY": get_int_env("PRINT_LABEL_TEXT_Y", 225),
        "textScaleX": get_int_env("PRINT_LABEL_TEXT_SCALE_X", 2),
        "textScaleY": get_int_env("PRINT_LABEL_TEXT_SCALE_Y", 2),
    }


def get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def ensure_success(code: int, action: str) -> None:
    if code == 0:
        return
    message = ERROR_MESSAGES.get(code, f"错误码 {code}")
    raise PrinterError(f"{action}失败：{message}")


def encode_text(value: str) -> bytes:
    return value.encode("gbk", errors="replace")


def estimate_text_width(value: str, scale: int) -> int:
    width = 0
    for char in value:
        width += 16 if ord(char) > 127 else 8
    return width * max(scale, 1)


class DDPrintSdk:
    def __init__(self, dll_path: Path):
        available, reason = get_availability()
        if not available:
            raise PrinterUnavailable(reason or "打印 SDK 不可用")

        self.pid = get_int_env("PRINT_PRINTER_PID", DEFAULT_PRINTER_PID)
        self.vid = get_int_env("PRINT_PRINTER_VID", DEFAULT_PRINTER_VID)
        self.dll_path = dll_path
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(dll_path.parent))
        self.dll = ctypes.CDLL(str(dll_path))
        self.configure_signatures()

    def configure_signatures(self) -> None:
        self.dll.startConnect.argtypes = [ctypes.c_long, ctypes.c_long]
        self.dll.startConnect.restype = ctypes.c_int
        self.dll.setSize.argtypes = [ctypes.c_float, ctypes.c_float]
        self.dll.setSize.restype = ctypes.c_int
        self.dll.setSpeed.argtypes = [ctypes.c_int]
        self.dll.setSpeed.restype = ctypes.c_int
        self.dll.setDensity.argtypes = [ctypes.c_int]
        self.dll.setDensity.restype = ctypes.c_int
        self.dll.clearCache.argtypes = []
        self.dll.clearCache.restype = ctypes.c_int
        self.dll.drawQRCode.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_ubyte,
            ctypes.c_int,
            ctypes.c_char_p,
        ]
        self.dll.drawQRCode.restype = ctypes.c_int
        self.dll.drawText.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p,
        ]
        self.dll.drawText.restype = ctypes.c_int
        self.dll.executePrint.argtypes = [ctypes.c_int]
        self.dll.executePrint.restype = ctypes.c_int

    def connect(self) -> None:
        ensure_success(self.dll.startConnect(self.pid, self.vid), "连接打印机")

    def print_qr_name_label(self, *, label_code: str, product_name: str, copies: int) -> None:
        if not label_code:
            raise PrinterError("标签编码不能为空")
        if not product_name:
            raise PrinterError("产品名称不能为空")

        layout = get_label_layout()
        ensure_success(
            self.dll.setSize(float(layout["widthMm"]), float(layout["heightMm"])),
            "设置标签尺寸",
        )
        ensure_success(self.dll.setSpeed(get_int_env("PRINT_LABEL_SPEED", 5)), "设置打印速度")
        ensure_success(self.dll.setDensity(get_int_env("PRINT_LABEL_DENSITY", 8)), "设置打印浓度")
        ensure_success(self.dll.clearCache(), "清空打印缓存")
        ensure_success(
            self.dll.drawQRCode(
                layout["qrX"],
                layout["qrY"],
                1,
                layout["qrCellWidth"],
                0,
                label_code.encode("utf-8"),
            ),
            "绘制二维码",
        )

        text_x = max(
            (layout["widthMm"] * layout["dotsPerMm"] - estimate_text_width(product_name, layout["textScaleX"])) // 2,
            0,
        )
        ensure_success(
            self.dll.drawText(
                text_x,
                layout["textY"],
                0,
                layout["textScaleX"],
                layout["textScaleY"],
                encode_text(product_name),
            ),
            "绘制产品名称",
        )
        ensure_success(self.dll.executePrint(copies), "执行打印")
