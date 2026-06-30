from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    CreateProductRequest,
    EmptyRequest,
    InspectReceiptRequest,
    InboundStockRequest,
    LabelInboundRequest,
    LabelOutboundRequest,
    OutboundStockRequest,
    PullOrdersRequest,
    SimulateOrderRequest,
    UpdateProductRequest,
)
from .services import (
    BusinessError,
    create_product,
    delete_inventory_label,
    delete_product,
    get_dashboard,
    get_inventory_system,
    get_logistics,
    inbound_with_labels,
    inbound_stock,
    inspect_receipt,
    list_orders,
    list_platforms,
    list_products,
    outbound_by_label,
    outbound_stock,
    pull_platform_orders,
    reset_system_data,
    sell_product,
    ship_order,
    update_product,
)

app = FastAPI(title="直播电商订单物流库存同步系统", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "live-commerce-sync-system",
    }


@app.get("/api/dashboard")
async def dashboard() -> dict:
    return get_dashboard()


@app.get("/api/platforms")
async def platforms() -> dict:
    return {"platforms": list_platforms()}


@app.get("/api/products")
async def products() -> dict:
    return {"products": list_products()}


@app.post("/api/products", status_code=201)
async def create_product_api(payload: CreateProductRequest) -> dict:
    try:
        product = create_product(payload.model_dump())
        return {
            "product": product,
            "dashboard": get_dashboard(),
        }
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.put("/api/products/{sku_id}")
async def update_product_api(sku_id: str, payload: UpdateProductRequest) -> dict:
    try:
        product = update_product(sku_id, payload.model_dump())
        return {
            "product": product,
            "dashboard": get_dashboard(),
        }
    except BusinessError as error:
        raise HTTPException(status_code=404 if str(error) == "商品不存在" else 400, detail=str(error)) from error


@app.delete("/api/products/{sku_id}")
async def delete_product_api(sku_id: str) -> dict:
    try:
        product = delete_product(sku_id)
        return {
            "product": product,
            "dashboard": get_dashboard(),
        }
    except BusinessError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/orders")
async def orders() -> dict:
    return {"orders": list_orders()}


@app.get("/api/logistics/{order_id}")
async def logistics(order_id: str) -> dict:
    try:
        return await get_logistics(order_id)
    except BusinessError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/api/orders/simulate", status_code=201)
async def simulate_order(payload: SimulateOrderRequest) -> dict:
    try:
        order = sell_product(
            platform_id=payload.platformId,
            sku_id=payload.skuId,
            quantity=payload.quantity,
            buyer=payload.buyer,
            source="manual",
        )
        return {
            "order": order,
            "dashboard": get_dashboard(),
        }
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/inventory/inbound", status_code=201)
async def inbound_inventory(payload: InboundStockRequest) -> dict:
    try:
        product = inbound_stock(
            sku_id=payload.skuId,
            quantity=payload.quantity,
            batch_no=payload.batchNo,
            production_date=payload.productionDate,
            expiry_date=payload.expiryDate,
            supplier=payload.supplier,
            warehouse=payload.warehouse,
            location=None,
            quality_result=payload.qualityResult,
            purchase_order_no=payload.purchaseOrderNo,
            operator=payload.operator,
        )
        return {
            "product": product,
            "dashboard": get_dashboard(),
        }
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/inventory/inspect", status_code=201)
async def inspect_inventory(payload: InspectReceiptRequest) -> dict:
    try:
        receipt = inspect_receipt(
            product_name=payload.productName,
            qualified_quantity=payload.qualifiedQuantity,
            inspector=payload.inspector,
        )
        return {
            "receipt": receipt,
            "dashboard": get_dashboard(),
        }
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/inventory/labels/inbound", status_code=201)
async def inbound_labels(payload: LabelInboundRequest) -> dict:
    try:
        result = inbound_with_labels(
            receipt_id=payload.receiptId,
            product_mode=payload.productMode,
            sku_id=payload.skuId,
            product_name=payload.productName,
            operator=payload.operator,
        )
        return {
            **result,
            "dashboard": get_dashboard(),
        }
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/inventory/labels/outbound", status_code=201)
async def outbound_label(payload: LabelOutboundRequest) -> dict:
    try:
        result = outbound_by_label(
            label_code=payload.labelCode,
            reason_id=payload.reasonId,
            operator=payload.operator,
            remark=payload.remark,
        )
        return {
            **result,
            "dashboard": get_dashboard(),
        }
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.delete("/api/inventory/labels/{label_code}")
async def delete_label_api(label_code: str) -> dict:
    try:
        result = delete_inventory_label(label_code)
        return {
            **result,
            "dashboard": get_dashboard(),
        }
    except BusinessError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/api/inventory/outbound", status_code=201)
async def outbound_inventory(payload: OutboundStockRequest) -> dict:
    try:
        result = outbound_stock(
            sku_id=payload.skuId,
            quantity=payload.quantity,
            channel_id=payload.channelId,
            outbound_type=payload.outboundType,
            recipient=payload.recipient,
            operator=payload.operator,
            remark=payload.remark,
        )
        return {
            **result,
            "dashboard": get_dashboard(),
        }
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/inventory/system")
async def inventory_system() -> dict:
    return get_inventory_system()


@app.post("/api/orders/pull", status_code=201)
async def pull_orders(payload: PullOrdersRequest | EmptyRequest | None = None) -> dict:
    try:
        platform_id = payload.platformId if isinstance(payload, PullOrdersRequest) else None
        return await pull_platform_orders(platform_id)
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/orders/{order_id}/ship")
async def ship(order_id: str) -> dict:
    try:
        order = ship_order(order_id)
        logistics_data = await get_logistics(order_id)
        return {
            "order": order,
            "events": logistics_data["events"],
        }
    except BusinessError as error:
        status_code = 404 if str(error) == "订单不存在" else 409
        raise HTTPException(status_code=status_code, detail=str(error)) from error


@app.post("/api/inventory/reset")
async def reset_inventory(_: EmptyRequest | None = None) -> dict:
    return reset_system_data()
