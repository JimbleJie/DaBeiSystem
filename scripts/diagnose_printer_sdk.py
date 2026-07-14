import ctypes
import os
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DLL_PATH = Path(os.getenv("PRINT_SDK_DLL", ROOT / "printer-sdk" / "printSDK" / "DDPrintSDK.dll"))
VID = int(os.getenv("PRINT_PRINTER_VID", "10473"))
PID = int(os.getenv("PRINT_PRINTER_PID", "656"))


def print_section(title: str) -> None:
    print(f"\n== {title} ==")


def run_command(command: list[str]) -> None:
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError as error:
        print(f"{command[0]} not available: {error}")
        return

    output = (result.stdout or "") + (result.stderr or "")
    print(output.strip() or f"exit code: {result.returncode}")


def configure(dll: ctypes.CDLL) -> None:
    dll.startConnect.argtypes = [ctypes.c_long, ctypes.c_long]
    dll.startConnect.restype = ctypes.c_int
    dll.connectPrinter.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_int]
    dll.connectPrinter.restype = ctypes.c_int
    dll.isConnectPrinter.argtypes = [ctypes.c_long, ctypes.c_long]
    dll.isConnectPrinter.restype = ctypes.c_int
    dll.disconnectPrinter.argtypes = []
    dll.disconnectPrinter.restype = ctypes.c_int
    dll.queryVidPid.argtypes = []
    dll.queryVidPid.restype = ctypes.c_int
    dll.sdkVersion.argtypes = []
    dll.sdkVersion.restype = ctypes.c_char_p


def call(name: str, func, *args: int) -> None:
    try:
        print(f"{name}{args} -> {func(*args)}")
    except Exception as error:
        print(f"{name}{args} raised {type(error).__name__}: {error}")


def main() -> int:
    print_section("Runtime")
    print(f"python: {sys.executable}")
    print(f"python bits: {platform.architecture()[0]}")
    print(f"platform: {sys.platform}")
    print(f"dll: {DLL_PATH}")
    print(f"dll exists: {DLL_PATH.exists()}")
    print(f"configured VID/PID: {VID}/{PID} (hex {VID:04X}/{PID:04X})")

    if os.name != "nt":
        print("This diagnostic must run on the Windows backend machine.")
        return 1

    print_section("USB devices")
    run_command([
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -like 'USB\\VID_*' } | Select-Object FriendlyName,InstanceId | Format-List",
    ])

    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(DLL_PATH.parent))
    dll = ctypes.CDLL(str(DLL_PATH))
    configure(dll)

    print_section("SDK")
    try:
        version = dll.sdkVersion()
        print(f"sdkVersion -> {version.decode('ascii', errors='replace') if version else version}")
    except Exception as error:
        print(f"sdkVersion raised {type(error).__name__}: {error}")

    print_section("Connection probes")
    call("disconnectPrinter", dll.disconnectPrinter)
    call("isConnectPrinter VID/PID", dll.isConnectPrinter, VID, PID)
    call("isConnectPrinter PID/VID", dll.isConnectPrinter, PID, VID)
    call("startConnect VID/PID", dll.startConnect, VID, PID)
    call("queryVidPid", dll.queryVidPid)
    call("disconnectPrinter", dll.disconnectPrinter)
    call("startConnect PID/VID (SDK order)", dll.startConnect, PID, VID)
    call("queryVidPid", dll.queryVidPid)
    call("disconnectPrinter", dll.disconnectPrinter)
    call("connectPrinter VID/PID/0", dll.connectPrinter, VID, PID, 0)
    call("queryVidPid", dll.queryVidPid)
    call("disconnectPrinter", dll.disconnectPrinter)
    call("connectPrinter PID/VID/0 (SDK order)", dll.connectPrinter, PID, VID, 0)
    call("queryVidPid", dll.queryVidPid)
    call("disconnectPrinter", dll.disconnectPrinter)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
