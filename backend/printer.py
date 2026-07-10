import ctypes
import os
import platform
import sys
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4

from .storage import ROOT, delete_state, load_json_state, save_json_state


DEFAULT_PRINTER_PID = 672
DEFAULT_PRINTER_VID = 10473
DEFAULT_LABEL_WIDTH_MM = 30
DEFAULT_LABEL_HEIGHT_MM = 40
DEFAULT_DOTS_PER_MM = 8
DEFAULT_QR_CELL_WIDTH = 5
DEFAULT_LABEL_CODE_Y = 182
DEFAULT_LABEL_CODE_SCALE_X = 1
DEFAULT_LABEL_CODE_SCALE_Y = 1
MIL_PER_MM = 39.37007874015748

ERROR_MESSAGES = {
    -1: "打印异常",
    0: "成功",
    1: "未连接打印机",
    2: "打印机忙",
    3: "文件不存在",
}

_sdk_lock = threading.Lock()
_sdk: "DDPrintSdk | None" = None
LEGACY_PRINT_TEMPLATE_STATE_KEY = "print_template_layout"
PRINT_TEMPLATE_STATE_KEY = "print_templates"
DEFAULT_PRINT_TEMPLATE_ID = "default"
DEFAULT_PRINT_TEMPLATE_NAME = "默认模版"
PRINT_TEMPLATE_FLOAT_FIELDS = (
    "widthMm",
    "heightMm",
    "qrDensityMil",
)
PRINT_TEMPLATE_NUMERIC_FIELDS = (
    "dotsPerMm",
    "printSpeed",
    "printDensity",
    "barcodeX",
    "barcodeY",
    "barcodeWidth",
    "barcodeHeight",
    "barcodeRotation",
    "qrModules",
    "qrX",
    "qrY",
    "qrCellWidth",
    "qrMode",
    "qrEccLevel",
    "qrQuietZoneModules",
    "qrRotation",
    "codeX",
    "codeY",
    "codeScaleX",
    "codeScaleY",
    "codeRotation",
    "textX",
    "textY",
    "textScaleX",
    "textScaleY",
    "textRotation",
)
PRINT_TEMPLATE_STRING_FIELDS = (
    "qrEncoding",
)
PRINT_TEMPLATE_BOOLEAN_FIELDS = (
    "showBarcode",
    "showQrCode",
    "showLabelCode",
    "showProductName",
)
PRINT_TEMPLATE_FIELDS = (
    "name",
    *PRINT_TEMPLATE_FLOAT_FIELDS,
    *PRINT_TEMPLATE_NUMERIC_FIELDS,
    *PRINT_TEMPLATE_STRING_FIELDS,
    *PRINT_TEMPLATE_BOOLEAN_FIELDS,
)


class PrinterUnavailable(Exception):
    pass


class PrinterError(Exception):
    pass


class PrintTemplateNotFound(Exception):
    pass


def print_labels(labels: list[dict[str, Any]], copies: int = 1, template_id: str | None = None) -> dict[str, Any]:
    if not labels:
        raise PrinterError("没有可打印的标签")
    if copies <= 0:
        raise PrinterError("打印份数必须大于 0")

    template = get_print_template(template_id)
    sdk = get_sdk()
    printed = 0
    with _sdk_lock:
        sdk.connect()
        for label in labels:
            sdk.print_qr_name_label(
                label_code=str(label.get("labelCode") or ""),
                product_name=str(label.get("productName") or ""),
                layout=template["layout"],
                copies=copies,
            )
            printed += 1

    return {
        "printed": printed,
        "copies": copies,
        "template": {
            "id": template["id"],
            "name": template["name"],
        },
        "layout": template["layout"],
    }


def get_printer_status(template_id: str | None = None) -> dict[str, Any]:
    enabled = is_printing_enabled()
    available, reason = get_availability()
    template = get_print_template(template_id)
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
        "templateId": template["id"],
        "templateName": template["name"],
        "layout": template["layout"],
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


def get_default_label_layout() -> dict[str, Any]:
    width_mm = get_float_env("PRINT_LABEL_WIDTH_MM", DEFAULT_LABEL_WIDTH_MM)
    height_mm = get_float_env("PRINT_LABEL_HEIGHT_MM", DEFAULT_LABEL_HEIGHT_MM)
    dots_per_mm = get_int_env("PRINT_LABEL_DOTS_PER_MM", DEFAULT_DOTS_PER_MM)
    qr_density_mil = get_float_env("PRINT_LABEL_QR_DENSITY_MIL", 24.63)
    qr_cell_width = get_int_env("PRINT_LABEL_QR_CELL_WIDTH", mil_to_dots(qr_density_mil, dots_per_mm))
    width_dots = int(round(width_mm * dots_per_mm))

    qr_modules = get_int_env("PRINT_LABEL_QR_MODULES", 25)
    qr_size = qr_modules * qr_cell_width
    qr_x = get_int_env("PRINT_LABEL_QR_X", max((width_dots - qr_size) // 2, 0))

    return {
        "widthMm": width_mm,
        "heightMm": height_mm,
        "dotsPerMm": dots_per_mm,
        "printSpeed": get_int_env("PRINT_LABEL_SPEED", 8),
        "printDensity": get_int_env("PRINT_LABEL_DENSITY", 4),
        "barcodeX": get_int_env("PRINT_LABEL_BARCODE_X", qr_x),
        "barcodeY": get_int_env("PRINT_LABEL_BARCODE_Y", get_int_env("PRINT_LABEL_QR_Y", 18)),
        "barcodeWidth": get_int_env("PRINT_LABEL_BARCODE_WIDTH", max(width_dots - qr_x * 2, 120)),
        "barcodeHeight": get_int_env("PRINT_LABEL_BARCODE_HEIGHT", max(int(qr_size * 0.45), 40)),
        "barcodeRotation": get_int_env("PRINT_LABEL_BARCODE_ROTATION", 0),
        "qrModules": qr_modules,
        "qrX": qr_x,
        "qrY": get_int_env("PRINT_LABEL_QR_Y", 18),
        "qrDensityMil": qr_density_mil,
        "qrCellWidth": qr_cell_width,
        "qrMode": get_int_env("PRINT_LABEL_QR_MODE", 0),
        "qrEncoding": os.getenv("PRINT_LABEL_QR_ENCODING", "ansi"),
        "qrEccLevel": get_int_env("PRINT_LABEL_QR_ECC_LEVEL", 2),
        "qrQuietZoneModules": get_int_env("PRINT_LABEL_QR_QUIET_ZONE_MODULES", 4),
        "qrRotation": get_int_env("PRINT_LABEL_QR_ROTATION", 0),
        "codeX": get_int_env("PRINT_LABEL_CODE_X", -1),
        "codeY": get_int_env("PRINT_LABEL_CODE_Y", DEFAULT_LABEL_CODE_Y),
        "codeScaleX": get_int_env("PRINT_LABEL_CODE_SCALE_X", DEFAULT_LABEL_CODE_SCALE_X),
        "codeScaleY": get_int_env("PRINT_LABEL_CODE_SCALE_Y", DEFAULT_LABEL_CODE_SCALE_Y),
        "codeRotation": get_int_env("PRINT_LABEL_CODE_ROTATION", 0),
        "textX": get_int_env("PRINT_LABEL_TEXT_X", -1),
        "textY": get_int_env("PRINT_LABEL_TEXT_Y", 225),
        "textScaleX": get_int_env("PRINT_LABEL_TEXT_SCALE_X", 2),
        "textScaleY": get_int_env("PRINT_LABEL_TEXT_SCALE_Y", 2),
        "textRotation": get_int_env("PRINT_LABEL_TEXT_ROTATION", 0),
        "showBarcode": False,
        "showQrCode": True,
        "showLabelCode": True,
        "showProductName": True,
    }


def normalize_label_layout(layout: dict[str, Any]) -> dict[str, Any]:
    defaults = get_default_label_layout()
    normalized: dict[str, Any] = {}
    for field in PRINT_TEMPLATE_FLOAT_FIELDS:
        value = layout.get(field, defaults[field])
        normalized[field] = float(value)
    for field in PRINT_TEMPLATE_NUMERIC_FIELDS:
        value = layout.get(field, defaults[field])
        normalized[field] = int(value)
    for field in PRINT_TEMPLATE_STRING_FIELDS:
        value = str(layout.get(field, defaults[field])).lower()
        normalized[field] = value if value in {"ansi", "utf-8"} else defaults[field]
    normalized["qrDensityMil"] = min(max(normalized["qrDensityMil"], 4), 100)
    normalized["qrCellWidth"] = min(max(mil_to_dots(normalized["qrDensityMil"], normalized["dotsPerMm"]), 1), 20)
    normalized["qrModules"] = max(normalized["qrModules"], 21)
    normalized["qrMode"] = 1 if normalized["qrMode"] == 1 else 0
    normalized["qrEccLevel"] = min(max(normalized["qrEccLevel"], 1), 4)
    normalized["qrQuietZoneModules"] = min(max(normalized["qrQuietZoneModules"], 0), 8)
    normalized["printDensity"] = min(max(normalized["printDensity"], 1), 15)
    normalized["printSpeed"] = min(max(normalized["printSpeed"], 1), 10)
    normalized["qrX"] = max(normalized["qrX"], 0)
    normalized["qrY"] = max(normalized["qrY"], 0)
    for field in PRINT_TEMPLATE_BOOLEAN_FIELDS:
        value = layout.get(field, defaults[field])
        normalized[field] = bool(value)
    return normalized


def build_print_template(template_id: str, name: str, layout: dict[str, Any], *, is_default: bool) -> dict[str, Any]:
    return {
        "id": template_id,
        "name": name,
        "isDefault": is_default,
        "layout": normalize_label_layout(layout),
    }


def get_default_print_template() -> dict[str, Any]:
    return build_print_template(
        DEFAULT_PRINT_TEMPLATE_ID,
        DEFAULT_PRINT_TEMPLATE_NAME,
        get_default_label_layout(),
        is_default=True,
    )


def migrate_legacy_print_template() -> None:
    current_state = load_json_state(PRINT_TEMPLATE_STATE_KEY, None)
    if current_state:
        return

    legacy_layout = load_json_state(LEGACY_PRINT_TEMPLATE_STATE_KEY, None)
    if not isinstance(legacy_layout, dict):
        return

    save_json_state(
        PRINT_TEMPLATE_STATE_KEY,
        {
            "templates": [
                {
                    "id": f"tpl-{uuid4().hex[:10]}",
                    "name": "迁移模版",
                    "layout": normalize_label_layout(legacy_layout),
                }
            ]
        },
    )
    delete_state(LEGACY_PRINT_TEMPLATE_STATE_KEY)


def get_saved_print_templates() -> list[dict[str, Any]]:
    migrate_legacy_print_template()
    saved = load_json_state(PRINT_TEMPLATE_STATE_KEY, {})
    templates = saved.get("templates") if isinstance(saved, dict) else []
    if not isinstance(templates, list):
        return []

    normalized_templates: list[dict[str, Any]] = []
    for item in templates:
        if not isinstance(item, dict):
            continue
        template_id = str(item.get("id") or f"tpl-{uuid4().hex[:10]}")
        name = str(item.get("name") or "自定义模版").strip() or "自定义模版"
        layout = item.get("layout") if isinstance(item.get("layout"), dict) else item
        normalized_templates.append(build_print_template(template_id, name, layout, is_default=False))
    return normalized_templates


def save_print_templates(templates: list[dict[str, Any]]) -> None:
    save_json_state(
        PRINT_TEMPLATE_STATE_KEY,
        {
            "templates": [
                {
                    "id": template["id"],
                    "name": template["name"],
                    "layout": normalize_label_layout(template["layout"]),
                }
                for template in templates
            ]
        },
    )


def list_print_templates() -> list[dict[str, Any]]:
    return [get_default_print_template(), *get_saved_print_templates()]


def get_print_template(template_id: str | None = None) -> dict[str, Any]:
    templates = list_print_templates()
    if not template_id:
        return templates[0]

    for template in templates:
        if template["id"] == template_id:
            return template

    raise PrintTemplateNotFound(f"print template not found: {template_id}")


def get_label_layout(template_id: str | None = None) -> dict[str, int]:
    return get_print_template(template_id)["layout"]


def get_print_template_settings(editor_template_id: str | None = None) -> dict[str, Any]:
    templates = list_print_templates()
    selected = templates[0]
    if editor_template_id:
        selected = get_print_template(editor_template_id)
    elif len(templates) > 1:
        selected = templates[1]

    return {
        "templates": templates,
        "editorTemplateId": selected["id"],
        "status": get_printer_status(selected["id"]),
    }


def create_print_template(payload: dict[str, Any]) -> dict[str, Any]:
    templates = get_saved_print_templates()
    template = build_print_template(
        f"tpl-{uuid4().hex[:10]}",
        str(payload.get("name") or "自定义模版").strip() or "自定义模版",
        payload,
        is_default=False,
    )
    templates.append(template)
    save_print_templates(templates)
    return get_print_template_settings(template["id"])


def update_print_template(template_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    if template_id == DEFAULT_PRINT_TEMPLATE_ID:
        raise PrinterError("default template cannot be overwritten")

    templates = get_saved_print_templates()
    updated = False
    for template in templates:
        if template["id"] == template_id:
            template["name"] = str(payload.get("name") or template["name"]).strip() or template["name"]
            template["layout"] = normalize_label_layout(payload)
            updated = True
            break

    if not updated:
        raise PrintTemplateNotFound(f"print template not found: {template_id}")

    save_print_templates(templates)
    return get_print_template_settings(template_id)


def delete_print_template_by_id(template_id: str) -> dict[str, Any]:
    if template_id == DEFAULT_PRINT_TEMPLATE_ID:
        raise PrinterError("default template cannot be deleted")

    templates = get_saved_print_templates()
    next_templates = [template for template in templates if template["id"] != template_id]
    if len(next_templates) == len(templates):
        raise PrintTemplateNotFound(f"print template not found: {template_id}")

    if next_templates:
        save_print_templates(next_templates)
    else:
        delete_state(PRINT_TEMPLATE_STATE_KEY)
    return get_print_template_settings()


def get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def get_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if not raw_value:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


def mil_to_dots(value: float, dots_per_mm: int) -> int:
    return max(1, int(round((float(value) / MIL_PER_MM) * max(int(dots_per_mm), 1))))


def ensure_success(code: int, action: str) -> None:
    if code == 0:
        return
    message = ERROR_MESSAGES.get(code, f"错误码 {code}")
    raise PrinterError(f"{action}失败：{message}")


def encode_text(value: str) -> bytes:
    return value.encode("gbk", errors="replace")


def encode_qr_content(value: str, encoding: str) -> bytes:
    if encoding == "ansi":
        codec = "mbcs" if os.name == "nt" else "gbk"
    else:
        codec = "utf-8"
    return value.encode(codec, errors="replace")


def estimate_text_width(value: str, scale: int) -> int:
    width = 0
    for char in value:
        width += 16 if ord(char) > 127 else 8
    return width * max(scale, 1)


def get_layout_width_dots(layout: dict[str, Any]) -> int:
    return int(round(float(layout["widthMm"]) * int(layout["dotsPerMm"])))


def resolve_text_x(layout: dict[str, Any], value: str, x_field: str, scale_field: str) -> int:
    raw_x = int(layout.get(x_field, -1))
    if raw_x >= 0:
        return raw_x
    return max((get_layout_width_dots(layout) - estimate_text_width(value, int(layout[scale_field]))) // 2, 0)


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
        self.dll.drawBarCode.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p,
        ]
        self.dll.drawBarCode.restype = ctypes.c_int
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

    def print_qr_name_label(self, *, label_code: str, product_name: str, layout: dict[str, int], copies: int) -> None:
        if not label_code:
            raise PrinterError("标签编码不能为空")
        if not product_name:
            raise PrinterError("产品名称不能为空")

        ensure_success(
            self.dll.setSize(float(layout["widthMm"]), float(layout["heightMm"])),
            "设置标签尺寸",
        )
        ensure_success(self.dll.setSpeed(int(layout.get("printSpeed", get_int_env("PRINT_LABEL_SPEED", 8)))), "?????????")
        ensure_success(self.dll.setDensity(int(layout.get("printDensity", get_int_env("PRINT_LABEL_DENSITY", 4)))), "?????????")
        ensure_success(self.dll.clearCache(), "?????????")
        if layout.get("showBarcode", True):
            ensure_success(
                self.dll.drawBarCode(
                    int(layout["barcodeX"]),
                    int(layout["barcodeY"]),
                    layout["barcodeHeight"],
                    b"128",
                    2,
                    int(layout.get("barcodeRotation", 0)),
                    2,
                    layout["barcodeWidth"],
                    label_code.encode("utf-8"),
                ),
                "绘制条形码",
            )

        if layout.get("showQrCode", False):
            ensure_success(
                self.dll.drawQRCode(
                    int(layout["qrX"]),
                    int(layout["qrY"]),
                    int(layout.get("qrMode", 0)),
                    layout["qrCellWidth"],
                    int(layout.get("qrRotation", 0)),
                    encode_qr_content(label_code, str(layout.get("qrEncoding", "ansi"))),
                ),
                "绘制二维码",
            )

        if layout.get("showLabelCode", True):
            ensure_success(
                self.dll.drawText(
                    resolve_text_x(layout, label_code, "codeX", "codeScaleX"),
                    int(layout["codeY"]),
                    int(layout.get("codeRotation", 0)),
                    layout["codeScaleX"],
                    layout["codeScaleY"],
                    encode_text(label_code),
                ),
                "绘制标签编码",
            )

        if layout.get("showProductName", True):
            ensure_success(
                self.dll.drawText(
                    resolve_text_x(layout, product_name, "textX", "textScaleX"),
                    int(layout["textY"]),
                    int(layout.get("textRotation", 0)),
                    layout["textScaleX"],
                    layout["textScaleY"],
                    encode_text(product_name),
                ),
                "绘制产品名称",
            )
        ensure_success(self.dll.executePrint(copies), "执行打印")
