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

## 目录

```text
android/
  app/            原生 Android 库存 App
config/
  runtime.json    前后端主机、端口、API 路径配置
backend/
  main.py         FastAPI 路由入口
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
- 入库第二步：输入合格数量、不合格数量，选择入库人（小梅雨、六一）
- 入库第三步：点击创建并入库，给每个合格产品生成唯一二维码编码

二维码格式：

```text
产品名称_入库时间_随机码
```

## 后续接真实 API 的位置

后端 `backend/adapters.py` 里的 `MockPlatformAdapter` 是渠道适配层。后续接淘宝、抖音、小红书、微信电商、私域渠道真实 API 时，可以保留业务接口不变，只替换 adapter 的 `pull_orders`、`sync_inventory`、`get_logistics` 方法。
