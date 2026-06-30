# Android 库存 App

这是库存管理的原生 Android 实现，数据通过 FastAPI 后台读写。入口界面包含：

- 设置
- 刷新后台数据
- 入库
- 出库
- 库存展示

## 联调后台

先在工程根目录启动后台：

```bash
npm run backend
```

Android App 里点击 `设置`，填写后台地址后点 `保存并测试连接`。

- Android 模拟器访问本机后台：`10.0.2.2`，端口 `4000`，API 路径 `/api`
- 真机访问 Mac 后台：填写 Mac 的局域网 IP；同时需要把 `config/runtime.json` 里的 `host` 改成可被手机访问的地址，例如 `0.0.0.0` 或 Mac 局域网 IP，并重启后台

## 入库流程

1. 从后台已有产品里选择产品
   - 如果没有查到产品，请到后台添加
2. 输入合格数量，并选择入库人（小梅雨、六一）
3. 点击 `创建并入库`
   - App 调用 `/api/inventory/inspect` 创建核检批次
   - App 调用 `/api/inventory/labels/inbound` 给每一个合格品创建二维码标签并增加库存
   - 首页库存展示同步刷新

## 出库流程

1. 点击 `扫码出库`，扫描产品二维码
   - 扫描结果会自动填入 `扫码标签`
2. 选择出库原因，例如懂茶帝发货、线上平台发货、私域发货
3. 点击 `确认出库`
   - App 调用 `/api/inventory/labels/outbound`
   - 后台标记标签已出库，扣减库存，并记录剪标出库流水

## 打开方式

用 Android Studio 打开 `android/` 目录即可。
