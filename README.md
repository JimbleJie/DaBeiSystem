# 直播电商订单物流库存同步系统

这是一个前后端分离的模拟实现，用于验证多渠道订单、物流、库存同步流程。

## 功能

- 模拟接入淘宝、抖音、小红书、微信电商、私域渠道 API
- 聚合订单管理
- 统一库存管理
- 任意平台售出后，全平台库存同步扣减
- 商品入库后，全平台库存同步更新到最新库存
- 壶出入库流程：到货核检合格数量 -> 判断新旧产品并打印/绑定单件二维码标签 -> 扫码入库
- 发货出库流程：装盒前扫描单件标签 -> 选择出库原因（如懂茶帝、线上平台等）-> 扣减库存并标记标签已剪
- 标签生命周期：每个在库壶都有一个未剪掉的二维码标签，出库后标签状态变为已出库
- 模拟物流轨迹追踪
- 模拟从平台拉取订单
- 首页按“数据源接入 -> 数仓 BI 工作台 -> 分析应用”展示经营逻辑
- 工作台展示单量、库存数、流水金额核心指标
- 订单管理和库存管理分模块展示

## 启动

分别启动后端和前端：

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
npm run backend
npm run frontend
```

访问：

- 地址统一配置在 `config/runtime.json`
- 前端：`http://{host}:{frontend.port}`
- 库存管理：`http://{host}:{frontend.port}/inventory`
- 订单管理：`http://{host}:{frontend.port}/orders`
- 后端健康检查：`http://{host}:{backend.port}{backend.apiPath}/health`

## 数据存储

后台业务数据使用 SQLite 持久化，数据库文件位于：

```text
data/inventory.sqlite
```

产品、库存标签、入库单、出库单、订单和库存流水都会写入这个文件。更换电脑或上传 Git 时，把 `data/inventory.sqlite` 一起提交/拷贝即可保留已有数据。

数据库按业务实体建表，核心表包括：

- `products`
- `inventory_labels`
- `receipts`
- `orders`
- `stock_movements`
- `stock_events`

## 定期备份

后端启动后会自动定期备份 SQLite 数据库，备份文件位于：

```text
backups/
```

默认每 24 小时备份一次，最多保留最近 30 份。前端顶部提供“立即备份”按钮，也可以直接调用：

```bash
curl -X POST http://127.0.0.1:4000/api/backups
curl http://127.0.0.1:4000/api/backups
```

如需调整频率和保留数量，可在启动后端前设置环境变量：

```bash
INVENTORY_BACKUP_INTERVAL_SECONDS=86400
INVENTORY_BACKUP_RETENTION_COUNT=30
```

后期 Git 上传时，建议同时提交 `data/inventory.sqlite` 和 `backups/` 中需要保留的备份文件。

## 打印 SDK

后台已预留 Windows 打印 SDK 接口，用于打印“二维码 + 产品名称”的单件标签。前端库存管理中的“打印”和“全部打印”会调用后端打印接口；当前不是 Windows 打印环境时，会自动打开浏览器打印预览。

默认 SDK 目录：

```text
printer-sdk/printSDK/DDPrintSDK.dll
```

也可以通过环境变量指定 SDK 目录：

```bash
PRINT_SDK_DIR="D:\\inventory-system\\printer-sdk\\printSDK"
```

默认打印模板：

- 标签尺寸：`30mm x 40mm`
- 内容：上方二维码，下方产品名称
- 默认 VID/PID：`10473 / 672`

可调整的环境变量：

```bash
PRINT_LABEL_WIDTH_MM=30
PRINT_LABEL_HEIGHT_MM=40
PRINT_LABEL_QR_X=45
PRINT_LABEL_QR_Y=18
PRINT_LABEL_QR_CELL_WIDTH=6
PRINT_LABEL_TEXT_Y=225
PRINT_LABEL_TEXT_SCALE_X=2
PRINT_LABEL_TEXT_SCALE_Y=2
PRINT_PRINTER_VID=10473
PRINT_PRINTER_PID=672
```

后端接口：

```text
GET  /api/printing/status
POST /api/printing/labels/{label_code}
POST /api/printing/products/{sku_id}
POST /api/printing/labels
```

## 目录

```text
android/
  app/            原生 Android 库存 App
config/
  runtime.json    前后端主机、端口、API 路径配置
data/
  inventory.sqlite SQLite 数据文件
backups/
  inventory_*.sqlite SQLite 备份文件
printer-sdk/
  printSDK/       Windows 打印 SDK 文件放置目录
backend/
  main.py         FastAPI 路由入口
  backup.py       SQLite 手动备份和定期备份
  printer.py      Windows 打印 SDK 封装
  services.py     订单、库存、物流业务逻辑
  adapters.py     模拟淘宝/抖音/小红书/微信电商/私域渠道 API
  schemas.py      请求参数模型
frontend/
  index.html      前端页面
  app.js          前端 API 调用和交互逻辑
  styles.css      前端样式
  server.js       前端静态资源服务器
```

## Android 库存 App

Android 版本在 `android/` 目录中，用 Android Studio 打开即可。

当前已实现移动端入库流程：

- 首页两个按钮：入库、出库
- 入库第一步：判断新品/老产品
- 入库第二步：输入合格数量，选择入库人（小梅雨、六一）
- 入库第三步：点击创建并入库，给每个合格产品生成唯一二维码编码

二维码格式：

```text
产品名称_入库时间_随机码
```

## 后续接真实 API 的位置

后端 `backend/adapters.py` 里的 `MockPlatformAdapter` 是渠道适配层。后续接淘宝、抖音、小红书、微信电商、私域渠道真实 API 时，可以保留业务接口不变，只替换 adapter 的 `pull_orders`、`sync_inventory`、`get_logistics` 方法。
