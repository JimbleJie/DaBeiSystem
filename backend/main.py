import sqlite3
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .backup import (
    create_database_backup,
    get_backup_status,
    list_database_backups,
    start_backup_scheduler,
    stop_backup_scheduler,
)
from .printer import (
    PrintTemplateNotFound,
    PrinterError,
    PrinterUnavailable,
    create_print_template,
    delete_print_template_by_id,
    get_print_template_settings,
    get_printer_status,
    print_labels,
    update_print_template,
)
from .schemas import (
    CreateProductRequest,
    EmptyRequest,
    InspectReceiptRequest,
    InboundStockRequest,
    LabelInboundRequest,
    LabelOutboundRequest,
    LabelReInboundRequest,
    OutboundStockRequest,
    PersonnelRequest,
    PrintLabelsRequest,
    PrintTemplateRequest,
    PullOrdersRequest,
    SimulateOrderRequest,
    UpdateProductRequest,
)
from .services import (
    BusinessError,
    create_personnel,
    create_product,
    delete_inventory_label,
    delete_personnel,
    delete_product,
    get_dashboard,
    get_inventory_label,
    get_inventory_system,
    list_personnel,
    get_logistics,
    get_print_label,
    inbound_with_labels,
    inbound_stock,
    list_print_labels_for_sku,
    inspect_receipt,
    list_orders,
    list_platforms,
    list_products,
    outbound_by_label,
    outbound_stock,
    pull_platform_orders,
    reinbound_by_label,
    reset_system_data,
    sell_product,
    ship_order,
    update_product,
)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    start_backup_scheduler()
    try:
        yield
    finally:
        stop_backup_scheduler()


app = FastAPI(title="直播电商订单物流库存同步系统", version="0.1.0", lifespan=lifespan)

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


@app.get("/api/backups")
async def backups() -> dict:
    return {
        "backups": list_database_backups(),
        "status": get_backup_status(),
    }


@app.get("/api/backups/status")
async def backup_status() -> dict:
    return get_backup_status()


@app.get("/api/printing/status")
async def printing_status() -> dict:
    return get_printer_status()


@app.get("/api/printing/template")
async def printing_template() -> dict:
    return get_print_template_settings()


@app.post("/api/printing/template")
async def create_printing_template(payload: PrintTemplateRequest) -> dict:
    return create_print_template(payload.model_dump())


@app.put("/api/printing/template/{template_id}")
async def update_printing_template(template_id: str, payload: PrintTemplateRequest) -> dict:
    try:
        return update_print_template(template_id, payload.model_dump())
    except PrintTemplateNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PrinterError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.delete("/api/printing/template/{template_id}")
async def delete_printing_template(template_id: str) -> dict:
    try:
        return delete_print_template_by_id(template_id)
    except PrintTemplateNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PrinterError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/printing/labels", status_code=201)
async def print_inventory_labels(payload: PrintLabelsRequest) -> dict:
    try:
        result = print_labels(
            [item.model_dump() for item in payload.labels],
            copies=payload.copies,
            template_id=payload.templateId,
        )
        return {
            "message": "打印任务已发送",
            **result,
        }
    except PrintTemplateNotFound as error:
        logger.warning("Print labels failed: template not found: %s", error)
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PrinterUnavailable as error:
        logger.warning("Print labels unavailable: %s", error)
        raise HTTPException(status_code=503, detail=str(error)) from error
    except PrinterError as error:
        logger.warning("Print labels rejected: %s", error)
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/printing/labels/{label_code}", status_code=201)
async def print_inventory_label(label_code: str) -> dict:
    try:
        result = print_labels([get_print_label(label_code)], copies=1)
        return {
            "message": "打印任务已发送",
            **result,
        }
    except BusinessError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PrinterUnavailable as error:
        logger.warning("Print label unavailable: %s", error)
        raise HTTPException(status_code=503, detail=str(error)) from error
    except PrinterError as error:
        logger.warning("Print label rejected: %s", error)
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/printing/products/{sku_id}", status_code=201)
async def print_product_inventory_labels(sku_id: str) -> dict:
    try:
        labels = list_print_labels_for_sku(sku_id)
        result = print_labels(labels, copies=1)
        return {
            "message": "打印任务已发送",
            **result,
        }
    except BusinessError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PrinterUnavailable as error:
        logger.warning("Print product labels unavailable: %s", error)
        raise HTTPException(status_code=503, detail=str(error)) from error
    except PrinterError as error:
        logger.warning("Print product labels rejected: %s", error)
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/backups", status_code=201)
async def create_backup() -> dict:
    try:
        backup = create_database_backup("manual")
        return {
            "backup": backup,
            "status": get_backup_status(),
        }
    except (OSError, sqlite3.Error) as error:
        raise HTTPException(status_code=500, detail=f"备份失败：{error}") from error


@app.get("/api/dashboard")
async def dashboard() -> dict:
    return get_dashboard()


@app.get("/api/platforms")
async def platforms() -> dict:
    return {"platforms": list_platforms()}


@app.get("/api/products")
async def products() -> dict:
    return {"products": list_products()}


@app.get("/api/personnel")
async def personnel() -> dict:
    return {"personnel": list_personnel()}


@app.post("/api/personnel", status_code=201)
async def create_personnel_api(payload: PersonnelRequest) -> dict:
    try:
        person = create_personnel(payload.name)
        return {
            "person": person,
            "personnel": list_personnel(),
            "dashboard": get_dashboard(),
        }
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.delete("/api/personnel/{person_id}")
async def delete_personnel_api(person_id: str) -> dict:
    try:
        person = delete_personnel(person_id)
        return {
            "person": person,
            "personnel": list_personnel(),
            "dashboard": get_dashboard(),
        }
    except BusinessError as error:
        status_code = 404 if str(error) == "人员不存在" else 400
        raise HTTPException(status_code=status_code, detail=str(error)) from error


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
            quality_grade=payload.qualityGrade,
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


@app.post("/api/inventory/labels/reinbound", status_code=201)
async def reinbound_label(payload: LabelReInboundRequest) -> dict:
    try:
        result = reinbound_by_label(
            label_code=payload.labelCode,
            operator=payload.operator,
            remark=payload.remark,
        )
        return {
            **result,
            "dashboard": get_dashboard(),
        }
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/inventory/labels/{label_code}")
async def get_label_api(label_code: str) -> dict:
    try:
        return get_inventory_label(label_code)
    except BusinessError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


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
