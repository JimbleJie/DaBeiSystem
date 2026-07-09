# Windows 打印 SDK 放置说明

将厂商 Windows SDK 中的 `printSDK` 目录复制到这里：

```text
printer-sdk/
  printSDK/
    DDPrintSDK.dll
    msvcp120.dll
    msvcr120.dll
```

当前后端默认从 `printer-sdk/printSDK/DDPrintSDK.dll` 加载打印 SDK。

注意：厂商提供的 `DDPrintSDK.dll` 是 32 位 Windows DLL。如果后端直接加载 DLL，需要使用 32 位 Python；如果使用 64 位 Python，建议改为 x86 C# 打印适配服务，再由 FastAPI 调用该服务。
