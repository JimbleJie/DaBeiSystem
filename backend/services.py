import random
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from .adapters import ADAPTERS, PLATFORMS, random_buyer, utc_now


class BusinessError(Exception):
    pass


def _initial_products() -> list[dict[str, Any]]:
    return [
        {
            "productId": "PRD-POT-001",
            "skuId": "POT-001",
            "name": "手作陶瓷壶",
            "spec": "600ml",
            "unit": "件",
            "category": "茶具",
            "barcode": "6900000000010",
            "price": 168,
            "centralStock": 10,
            "lockedStock": 0,
            "inTransitStock": 0,
            "safeStock": 3,
            "batchNo": "BATCH-TEA-001",
            "productionDate": "2026-06-01",
            "expiryDate": "2028-06-01",
            "supplier": "景德镇源头工厂",
            "warehouse": "杭州主仓",
            "location": "A-03-05",
            "qrCode": "QR-PRD-POT-001-BATCH-TEA-001",
        },
        {
            "productId": "PRD-CUP-002",
            "skuId": "CUP-002",
            "name": "配套品茗杯",
            "spec": "80ml",
            "unit": "件",
            "category": "茶具",
            "barcode": "6900000000027",
            "price": 39,
            "centralStock": 24,
            "lockedStock": 0,
            "inTransitStock": 0,
            "safeStock": 6,
            "batchNo": "BATCH-CUP-001",
            "productionDate": "2026-06-05",
            "expiryDate": "2028-06-05",
            "supplier": "景德镇源头工厂",
            "warehouse": "杭州主仓",
            "location": "A-03-06",
            "qrCode": "QR-PRD-CUP-002-BATCH-CUP-001",
        },
    ]


products = _initial_products()
orders: list[dict[str, Any]] = []
stock_events: list[dict[str, Any]] = [
    {
        "id": str(uuid4()),
        "type": "init",
        "message": "系统初始化库存，全部渠道库存镜像已同步",
        "createdAt": utc_now(),
    }
]
stock_movements: list[dict[str, Any]] = []
receipts: list[dict[str, Any]] = []
inventory_labels: list[dict[str, Any]] = []

OUTBOUND_CHANNELS = {
    "taobao": "淘宝渠道",
    "xiaohongshu": "小红书渠道",
    "distributor": "经销商渠道",
    "video": "视频号渠道",
    "private_domain": "私域渠道",
    "damage": "破损出库",
}

OUTBOUND_TYPES = {
    "channel_sale": "渠道销售出库",
    "return_to_supplier": "退供出库",
    "damage": "破损出库",
    "transfer": "调拨出库",
}

LABEL_OUTBOUND_REASONS = {
    "dongchadi": "懂茶帝发货",
    "online_platform": "线上平台发货",
    "taobao": "淘宝发货",
    "douyin": "抖音发货",
    "xiaohongshu": "小红书发货",
    "wechat": "微信电商发货",
    "private_domain": "私域发货",
    "offline": "线下发货",
}


def seed_inventory_labels() -> None:
    inventory_labels.clear()
    now = utc_now()
    for product in products:
        for index in range(product["centralStock"]):
            inventory_labels.append(
                {
                    "labelCode": f"QR-{product['skuId']}-{index + 1:04d}",
                    "skuId": product["skuId"],
                    "productName": product["name"],
                    "status": "in_stock",
                    "receiptId": "INITIAL",
                    "printedAt": now,
                    "inboundAt": now,
                    "outboundAt": "",
                    "outboundReason": "",
                    "operator": "系统初始化",
                }
            )


seed_inventory_labels()


def seed_demo_documents() -> None:
    demo_specs = [
        {
            "receiptId": "RCV-DEMO-POT-001",
            "skuId": "POT-001",
            "productName": "手作陶瓷壶",
            "qualifiedQuantity": 2,
            "rejectedQuantity": 1,
            "operator": "小梅雨",
            "outboundOperator": "六一",
            "outboundReason": "懂茶帝发货",
        },
        {
            "receiptId": "RCV-DEMO-CUP-002",
            "skuId": "CUP-002",
            "productName": "配套品茗杯",
            "qualifiedQuantity": 1,
            "rejectedQuantity": 0,
            "operator": "六一",
            "outboundOperator": "小梅雨",
            "outboundReason": "私域发货",
        },
    ]
    now = utc_now()

    for spec in demo_specs:
        product = find_product(spec["skuId"])
        if product is None:
            continue

        product["centralStock"] += spec["qualifiedQuantity"] - 1
        receipt = {
            "receiptId": spec["receiptId"],
            "productName": product["name"],
            "qualifiedQuantity": spec["qualifiedQuantity"],
            "rejectedQuantity": spec["rejectedQuantity"],
            "status": "inbound",
            "inspector": spec["operator"],
            "operator": spec["operator"],
            "skuId": product["skuId"],
            "labelCodes": [],
            "createdAt": now,
            "inboundAt": now,
        }
        receipts.insert(0, receipt)

        for index in range(spec["qualifiedQuantity"]):
            label_code = f"QR-{spec['receiptId']}-{index + 1:03d}"
            label = {
                "labelCode": label_code,
                "skuId": product["skuId"],
                "productName": product["name"],
                "status": "in_stock",
                "receiptId": spec["receiptId"],
                "printedAt": now,
                "inboundAt": now,
                "outboundAt": "",
                "outboundReason": "",
                "operator": spec["operator"],
            }
            receipt["labelCodes"].append(label_code)
            inventory_labels.insert(0, label)

        outbound_label = find_label(receipt["labelCodes"][0])
        if outbound_label:
            outbound_label["status"] = "outbound"
            outbound_label["outboundAt"] = now
            outbound_label["outboundReason"] = spec["outboundReason"]
            outbound_label["operator"] = spec["outboundOperator"]

def list_platforms() -> list[dict[str, str]]:
    return [platform.__dict__ for platform in PLATFORMS]


def list_products() -> list[dict[str, Any]]:
    return [serialize_product(product) for product in products]


def list_orders() -> list[dict[str, Any]]:
    return [serialize_order(order) for order in orders]


def get_dashboard() -> dict[str, Any]:
    return {
        "platforms": list_platforms(),
        "products": list_products(),
        "orders": list_orders(),
        "stockEvents": stock_events[:8],
        "stockMovements": stock_movements[:12],
        "receipts": receipts[:10],
        "inventoryLabels": inventory_labels[:80],
        "inboundDocuments": build_inbound_documents(),
        "outboundDocuments": build_outbound_documents(),
        "inventorySystem": get_inventory_system(),
        "metrics": {
            "totalOrders": len(orders),
            "paidOrders": len([order for order in orders if order["status"] == "paid"]),
            "shippedOrders": len([order for order in orders if order["status"] == "shipped"]),
            "totalInventory": sum(available_stock(product) for product in products),
            "totalAmount": round(sum(order["amount"] for order in orders), 2),
        },
    }


def sell_product(
    *,
    platform_id: str,
    sku_id: str,
    quantity: int,
    buyer: str | None = None,
    status: str = "paid",
    source: str = "manual",
    platform_order_id: str | None = None,
) -> dict[str, Any]:
    platform = next((item for item in PLATFORMS if item.id == platform_id), None)
    product = find_product(sku_id)

    if platform is None:
        raise BusinessError("平台不存在")

    if product is None:
        raise BusinessError("商品不存在")

    if quantity <= 0:
        raise BusinessError("购买数量必须为正整数")

    if available_stock(product) < quantity:
        raise BusinessError(f"{product['name']} 库存不足")

    product["centralStock"] -= quantity
    order = create_order(
        platform_id=platform_id,
        sku_id=sku_id,
        quantity=quantity,
        buyer=buyer or random_buyer(),
        status=status,
        logistics_status="待发货",
        source=source,
        platform_order_id=platform_order_id,
    )
    orders.insert(0, order)

    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "sale",
            "message": f"{platform.name} 售出 {product['name']} x {quantity}，全部渠道库存同步为 {available_stock(product)}",
            "platformId": platform_id,
            "skuId": sku_id,
            "quantity": quantity,
            "createdAt": utc_now(),
        },
    )
    record_stock_movement(
        movement_type="outbound",
        sku_id=sku_id,
        quantity=quantity,
        operator="系统",
        scene=f"{platform.name}销售出库",
        before_stock=product["centralStock"] + quantity,
        after_stock=product["centralStock"],
        warehouse=product.get("warehouse", "主仓"),
        location=product.get("location", "A-01-01"),
        reference_no=platform_order_id,
    )
    mark_labels_outbound_for_sale(
        sku_id=sku_id,
        quantity=quantity,
        reason=f"{platform.name}销售出库",
        operator="系统",
    )

    return order


def create_product(payload: dict[str, Any]) -> dict[str, Any]:
    sku_id = payload.get("skuId") or generate_sku_id(payload["name"])

    if find_product(sku_id) is not None:
        raise BusinessError("SKU 已存在")

    product_id = f"PRD-{sku_id}"
    batch_no = payload.get("batchNo") or f"BATCH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    initial_stock = int(payload.get("initialStock") or 0)
    now = utc_now()

    product = {
        "productId": product_id,
        "skuId": sku_id,
        "name": payload["name"],
        "spec": payload.get("spec") or "标准款",
        "unit": payload.get("unit") or "件",
        "category": payload.get("category") or "默认分类",
        "barcode": payload.get("barcode") or generate_barcode(),
        "price": float(payload.get("price") or 0),
        "centralStock": initial_stock,
        "lockedStock": 0,
        "inTransitStock": 0,
        "safeStock": int(payload.get("safeStock") or 0),
        "batchNo": batch_no,
        "productionDate": payload.get("productionDate") or "",
        "expiryDate": payload.get("expiryDate") or "",
        "supplier": payload.get("supplier") or "",
        "warehouse": payload.get("warehouse") or "主仓",
        "location": payload.get("location") or "A-01-01",
        "qrCode": f"QR-{product_id}-{batch_no}",
        "createdAt": now,
        "updatedAt": now,
    }
    products.append(product)

    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "new_product",
            "message": f"{product['name']} 完成新品建档并入库 {initial_stock} 件，二维码已绑定",
            "skuId": sku_id,
            "quantity": initial_stock,
            "createdAt": now,
        },
    )

    if initial_stock > 0:
        record_stock_movement(
            movement_type="inbound",
            sku_id=sku_id,
            quantity=initial_stock,
            operator=payload.get("operator") or "仓库管理员",
            scene="新品建档入库",
            before_stock=0,
            after_stock=initial_stock,
            warehouse=product["warehouse"],
            location=product["location"],
            reference_no=batch_no,
        )

    return serialize_product(product)


def update_product(sku_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    product = find_product(sku_id)
    if product is None:
        raise BusinessError("商品不存在")

    name = (payload.get("name") or "").strip()
    if not name:
        raise BusinessError("产品名称不能为空")

    product["name"] = name
    product["updatedAt"] = utc_now()

    for label in inventory_labels:
        if label.get("skuId") == sku_id:
            label["productName"] = name

    for receipt in receipts:
        if receipt.get("skuId") == sku_id:
            receipt["productName"] = name

    for order in orders:
        if order.get("skuId") == sku_id:
            order["productName"] = name

    for movement in stock_movements:
        if movement.get("skuId") == sku_id:
            movement["productName"] = name

    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "update_product",
            "message": f"产品 {sku_id} 已更新为 {name}",
            "skuId": sku_id,
            "quantity": 0,
            "createdAt": utc_now(),
        },
    )
    return serialize_product(product)


def delete_product(sku_id: str) -> dict[str, Any]:
    product = find_product(sku_id)
    if product is None:
        raise BusinessError("商品不存在")

    products.remove(product)
    removed_labels = [label for label in inventory_labels if label.get("skuId") == sku_id]
    inventory_labels[:] = [
        label for label in inventory_labels
        if label.get("skuId") != sku_id
    ]

    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "delete_product",
            "message": f"产品 {product['name']} 已删除，关联标签 {len(removed_labels)} 个已移除",
            "skuId": sku_id,
            "quantity": -int(product.get("centralStock") or 0),
            "createdAt": utc_now(),
        },
    )
    return serialize_product(product)


def delete_inventory_label(label_code: str) -> dict[str, Any]:
    label = find_label(label_code)
    if label is None:
        raise BusinessError("二维码标签不存在")

    product = find_product(label.get("skuId", ""))
    before_stock = product["centralStock"] if product else 0
    if product is not None and label.get("status") == "in_stock":
        product["centralStock"] = max(product["centralStock"] - 1, 0)
        product["updatedAt"] = utc_now()

    inventory_labels.remove(label)

    for receipt in receipts:
        label_codes = receipt.get("labelCodes")
        if isinstance(label_codes, list) and label_code in label_codes:
            label_codes.remove(label_code)

    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "delete_label",
            "message": f"二维码标签 {label_code} 已删除",
            "skuId": label.get("skuId", ""),
            "quantity": -1 if label.get("status") == "in_stock" else 0,
            "createdAt": utc_now(),
        },
    )

    if product is not None and label.get("status") == "in_stock":
        record_stock_movement(
            movement_type="delete_label",
            sku_id=product["skuId"],
            quantity=-1,
            operator="系统",
            scene="删除单件标签",
            before_stock=before_stock,
            after_stock=product["centralStock"],
            warehouse=product.get("warehouse", "主仓"),
            location=product.get("location", ""),
            reference_no=label_code,
        )

    return {
        "label": label,
        "product": serialize_product(product) if product else None,
    }


def inbound_stock(
    *,
    sku_id: str,
    quantity: int,
    batch_no: str | None = None,
    production_date: str | None = None,
    expiry_date: str | None = None,
    supplier: str | None = None,
    warehouse: str | None = None,
    location: str | None = None,
    quality_result: str | None = None,
    purchase_order_no: str | None = None,
    operator: str | None = None,
) -> dict[str, Any]:
    product = find_product(sku_id)

    if product is None:
        raise BusinessError("商品不存在")

    if quantity <= 0:
        raise BusinessError("入库数量必须为正整数")

    before_stock = product["centralStock"]
    product["centralStock"] += quantity
    product["batchNo"] = batch_no or product.get("batchNo", "")
    product["productionDate"] = production_date or product.get("productionDate", "")
    product["expiryDate"] = expiry_date or product.get("expiryDate", "")
    product["supplier"] = supplier or product.get("supplier", "")
    product["warehouse"] = warehouse or product.get("warehouse", "主仓")
    product["location"] = location or product.get("location", "A-01-01")
    product["updatedAt"] = utc_now()

    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "inbound",
            "message": f"{product['name']} 入库 {quantity} 件，全部渠道库存同步为 {available_stock(product)}",
            "skuId": sku_id,
            "quantity": quantity,
            "qualityResult": quality_result or "合格",
            "purchaseOrderNo": purchase_order_no or "",
            "createdAt": utc_now(),
        },
    )
    record_stock_movement(
        movement_type="inbound",
        sku_id=sku_id,
        quantity=quantity,
        operator=operator or "仓库管理员",
        scene="已有商品直接入库",
        before_stock=before_stock,
        after_stock=product["centralStock"],
        warehouse=product["warehouse"],
        location=product["location"],
        reference_no=purchase_order_no or product.get("batchNo", ""),
    )

    return serialize_product(product)


def inspect_receipt(*, product_name: str, qualified_quantity: int, rejected_quantity: int = 0, inspector: str | None = None) -> dict[str, Any]:
    receipt = {
        "receiptId": f"RCV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
        "productName": product_name,
        "qualifiedQuantity": qualified_quantity,
        "rejectedQuantity": rejected_quantity,
        "status": "inspected",
        "inspector": inspector or "质检员",
        "createdAt": utc_now(),
    }
    receipts.insert(0, receipt)
    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "inspection",
            "message": f"{product_name} 到货核检完成：合格 {qualified_quantity} 个，不合格 {rejected_quantity} 个",
            "createdAt": utc_now(),
        },
    )
    return receipt


def inbound_with_labels(
    *,
    receipt_id: str,
    product_mode: str,
    sku_id: str | None,
    product_name: str | None,
    operator: str | None = None,
) -> dict[str, Any]:
    receipt = find_receipt(receipt_id)
    if receipt is None:
        raise BusinessError("核检批次不存在")
    if receipt["status"] == "inbound":
        raise BusinessError("该批次已入库")

    if product_mode == "new":
        created = create_product(
            {
                "name": product_name or receipt["productName"],
                "spec": "标准款",
                "unit": "个",
                "category": "壶",
                "initialStock": 0,
                "safeStock": 2,
                "operator": operator or "入库员",
            }
        )
        sku_id = created["skuId"]
    elif not sku_id:
        raise BusinessError("请选择旧产品或创建新品")

    product = find_product(sku_id)
    if product is None:
        raise BusinessError("商品不存在")

    quantity = receipt["qualifiedQuantity"]
    before_stock = product["centralStock"]
    product["centralStock"] += quantity
    product["updatedAt"] = utc_now()
    labels = []

    for index in range(quantity):
        label = {
            "labelCode": f"QR-{receipt_id}-{index + 1:03d}",
            "skuId": product["skuId"],
            "productName": product["name"],
            "status": "in_stock",
            "receiptId": receipt_id,
            "printedAt": utc_now(),
            "inboundAt": utc_now(),
            "outboundAt": "",
            "outboundReason": "",
            "operator": operator or "入库员",
        }
        labels.append(label)
        inventory_labels.insert(0, label)

    receipt["status"] = "inbound"
    receipt["skuId"] = product["skuId"]
    receipt["productName"] = product["name"]
    receipt["operator"] = operator or "入库员"
    receipt["labelCodes"] = [label["labelCode"] for label in labels]
    receipt["inboundAt"] = utc_now()

    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "label_inbound",
            "message": f"{product['name']} 打印并绑定 {quantity} 个二维码标签，扫码入库完成",
            "skuId": product["skuId"],
            "quantity": quantity,
            "createdAt": utc_now(),
        },
    )
    record_stock_movement(
        movement_type="inbound",
        sku_id=product["skuId"],
        quantity=quantity,
        operator=operator or "入库员",
        scene="贴标扫码入库",
        before_stock=before_stock,
        after_stock=product["centralStock"],
        warehouse=product.get("warehouse", "主仓"),
        location=product.get("location", ""),
        reference_no=receipt_id,
        remark="每个合格品已贴二维码标签",
    )

    return {
        "receipt": receipt,
        "product": serialize_product(product),
        "labels": labels,
    }


def outbound_by_label(*, label_code: str, reason_id: str, operator: str | None = None, remark: str | None = None) -> dict[str, Any]:
    label = find_label(label_code)
    if label is None:
        raise BusinessError("二维码标签不存在")
    if label["status"] != "in_stock":
        raise BusinessError("该标签已出库，不能重复出库")

    product = find_product(label["skuId"])
    if product is None:
        raise BusinessError("标签对应商品不存在")
    if product["centralStock"] <= 0:
        raise BusinessError("库存不足，不能出库")

    reason = LABEL_OUTBOUND_REASONS.get(reason_id, reason_id)
    before_stock = product["centralStock"]
    product["centralStock"] -= 1
    product["updatedAt"] = utc_now()
    label["status"] = "outbound"
    label["outboundAt"] = utc_now()
    label["outboundReason"] = reason
    label["operator"] = operator or "出库员"

    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "label_outbound",
            "message": f"扫码出库 {product['name']} 1 个，原因：{reason}；装盒前剪掉标签",
            "skuId": product["skuId"],
            "quantity": 1,
            "createdAt": utc_now(),
        },
    )
    record_stock_movement(
        movement_type="outbound",
        sku_id=product["skuId"],
        quantity=1,
        operator=operator or "出库员",
        scene="扫码剪标出库",
        before_stock=before_stock,
        after_stock=product["centralStock"],
        warehouse=product.get("warehouse", "主仓"),
        location=product.get("location", ""),
        channel=reason,
        reference_no=label_code,
        remark=remark or "装盒前剪掉标签",
    )

    return {
        "label": label,
        "product": serialize_product(product),
        "movement": stock_movements[0],
    }


def outbound_stock(
    *,
    sku_id: str,
    quantity: int,
    channel_id: str,
    outbound_type: str,
    recipient: str | None = None,
    operator: str | None = None,
    remark: str | None = None,
) -> dict[str, Any]:
    product = find_product(sku_id)

    if product is None:
        raise BusinessError("商品不存在")

    if quantity <= 0:
        raise BusinessError("出库数量必须为正整数")

    if available_stock(product) < quantity:
        raise BusinessError(f"{product['name']} 可用库存不足")

    channel = next((item for item in PLATFORMS if item.id == channel_id), None)
    channel_name = channel.name if channel else OUTBOUND_CHANNELS.get(channel_id, channel_id)
    before_stock = product["centralStock"]
    product["centralStock"] -= quantity
    product["updatedAt"] = utc_now()
    outbound_no = f"OUT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"

    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "outbound",
            "message": f"{channel_name} 出库 {product['name']} x {quantity}，全部渠道库存同步为 {available_stock(product)}",
            "skuId": sku_id,
            "quantity": quantity,
            "channelId": channel_id,
            "outboundType": outbound_type,
            "createdAt": utc_now(),
        },
    )
    record_stock_movement(
        movement_type="outbound",
        sku_id=sku_id,
        quantity=quantity,
        operator=operator or "出库员",
        scene=OUTBOUND_TYPES.get(outbound_type, outbound_type),
        before_stock=before_stock,
        after_stock=product["centralStock"],
        warehouse=product.get("warehouse", "主仓"),
        location=product.get("location", "A-01-01"),
        channel=channel_name,
        reference_no=outbound_no,
        remark=remark or recipient or "",
    )

    return {
        "outboundNo": outbound_no,
        "product": serialize_product(product),
        "movement": stock_movements[0],
    }


async def pull_platform_orders(platform_id: str | None = None) -> dict[str, Any]:
    platform_ids = [platform_id] if platform_id else [platform.id for platform in PLATFORMS]
    pulled_orders: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for current_platform_id in platform_ids:
        adapter = ADAPTERS.get(current_platform_id)

        if adapter is None:
            failures.append({"platformId": current_platform_id, "message": "平台不存在"})
            continue

        platform_orders = await adapter.pull_orders(products)

        for platform_order in platform_orders:
            try:
                pulled_orders.append(
                    sell_product(
                        platform_id=platform_order["platformId"],
                        sku_id=platform_order["skuId"],
                        quantity=platform_order["quantity"],
                        buyer=platform_order["buyer"],
                        status=platform_order["status"],
                        source="platform-pull",
                        platform_order_id=platform_order["platformOrderId"],
                    )
                )
            except BusinessError as error:
                failures.append({"platformId": current_platform_id, "message": str(error)})

    return {
        "orders": [serialize_order(order) for order in pulled_orders],
        "failures": failures,
        "dashboard": get_dashboard(),
    }


def ship_order(order_id: str) -> dict[str, Any]:
    order = find_order(order_id)

    if order is None:
        raise BusinessError("订单不存在")

    if order["status"] == "shipped":
        raise BusinessError("订单已发货")

    order["status"] = "shipped"
    order["logisticsStatus"] = "运输中"
    order["trackingNo"] = f"YT{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    order["updatedAt"] = utc_now()

    return order


async def get_logistics(order_id: str) -> dict[str, Any]:
    order = find_order(order_id)

    if order is None:
        raise BusinessError("订单不存在")

    adapter = ADAPTERS[order["platformId"]]
    return {
        "order": serialize_order(order),
        "events": await adapter.get_logistics(order),
    }


def reset_demo() -> dict[str, Any]:
    products.clear()
    products.extend(_initial_products())
    orders.clear()
    stock_movements.clear()
    receipts.clear()
    seed_inventory_labels()
    seed_demo_documents()
    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "reset",
            "message": "已重置库存和订单",
            "createdAt": utc_now(),
        },
    )
    return get_dashboard()


def create_order(
    *,
    platform_id: str,
    sku_id: str,
    quantity: int,
    buyer: str,
    status: str,
    logistics_status: str,
    source: str,
    platform_order_id: str | None = None,
) -> dict[str, Any]:
    product = find_product(sku_id)
    now = utc_now()

    return {
        "orderId": str(uuid4()),
        "platformOrderId": platform_order_id or f"{platform_id.upper()}-{random.randint(100000, 999999)}",
        "platformId": platform_id,
        "skuId": sku_id,
        "productName": product["name"] if product else sku_id,
        "quantity": quantity,
        "amount": round((product["price"] if product else 0) * quantity, 2),
        "buyer": buyer,
        "status": status,
        "logisticsStatus": logistics_status,
        "trackingNo": "",
        "source": source,
        "createdAt": now,
        "updatedAt": now,
    }


def serialize_product(product: dict[str, Any]) -> dict[str, Any]:
    platform_inventory = {
        platform.id: {
            "platformName": platform.name,
            "availableStock": available_stock(product),
            "syncedAt": utc_now(),
        }
        for platform in PLATFORMS
    }

    return {
        **product,
        "availableStock": available_stock(product),
        "platformInventory": platform_inventory,
    }


def serialize_order(order: dict[str, Any]) -> dict[str, Any]:
    platform = next((item for item in PLATFORMS if item.id == order["platformId"]), None)
    return {
        **order,
        "platformName": platform.name if platform else order["platformId"],
    }


def find_product(sku_id: str) -> dict[str, Any] | None:
    return next((product for product in products if product["skuId"] == sku_id), None)


def find_order(order_id: str) -> dict[str, Any] | None:
    return next((order for order in orders if order["orderId"] == order_id), None)


def find_receipt(receipt_id: str) -> dict[str, Any] | None:
    return next((receipt for receipt in receipts if receipt["receiptId"] == receipt_id), None)


def find_label(label_code: str) -> dict[str, Any] | None:
    return next((label for label in inventory_labels if label["labelCode"] == label_code), None)


seed_demo_documents()


def mark_labels_outbound_for_sale(*, sku_id: str, quantity: int, reason: str, operator: str) -> None:
    available_labels = [
        label for label in inventory_labels
        if label["skuId"] == sku_id and label["status"] == "in_stock"
    ][:quantity]
    for label in available_labels:
        label["status"] = "outbound"
        label["outboundAt"] = utc_now()
        label["outboundReason"] = reason
        label["operator"] = operator


def available_stock(product: dict[str, Any]) -> int:
    return max(product["centralStock"] - product["lockedStock"], 0)


def build_inbound_documents() -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []

    for receipt in receipts:
        if receipt.get("status") != "inbound":
            continue

        receipt_labels = [
            label for label in inventory_labels
            if label.get("receiptId") == receipt["receiptId"]
        ]
        product = find_product(receipt.get("skuId", ""))
        documents.append(
            {
                "documentId": receipt["receiptId"],
                "productName": product["name"] if product else receipt.get("productName", ""),
                "qualifiedQuantity": receipt.get("qualifiedQuantity", 0),
                "rejectedQuantity": receipt.get("rejectedQuantity", 0),
                "operator": receipt.get("operator") or receipt.get("inspector", "入库员"),
                "inboundAt": receipt.get("inboundAt") or receipt.get("createdAt", ""),
                "qrCodes": [label["labelCode"] for label in receipt_labels],
            }
        )

    return sorted(documents, key=lambda item: item.get("inboundAt", ""), reverse=True)


def build_outbound_documents() -> list[dict[str, Any]]:
    documents = [
        {
            "documentId": label["labelCode"],
            "productName": label.get("productName", ""),
            "outboundDate": label.get("outboundAt", ""),
            "productCode": label["labelCode"],
            "operator": label.get("operator", "出库员"),
            "outboundReason": label.get("outboundReason", ""),
        }
        for label in inventory_labels
        if label.get("status") == "outbound"
    ]

    return sorted(documents, key=lambda item: item.get("outboundDate", ""), reverse=True)


def get_inventory_system() -> dict[str, Any]:
    total_stock = sum(product["centralStock"] for product in products)
    available = sum(available_stock(product) for product in products)
    frozen = sum(product.get("lockedStock", 0) for product in products)
    in_transit = sum(product.get("inTransitStock", 0) for product in products)
    warehouses = sorted({product.get("warehouse", "主仓") for product in products})

    return {
        "engine": {
            "totalStock": total_stock,
            "availableStock": available,
            "frozenStock": frozen,
            "inTransitStock": in_transit,
            "skuCount": len(products),
            "warehouseCount": len(warehouses),
        },
        "alerts": build_inventory_alerts(),
        "movements": stock_movements[:12],
        "auditLogs": stock_events[:12],
        "outboundChannels": [
            {"id": channel_id, "name": channel_name}
            for channel_id, channel_name in OUTBOUND_CHANNELS.items()
        ],
        "outboundTypes": [
            {"id": outbound_type, "name": type_name}
            for outbound_type, type_name in OUTBOUND_TYPES.items()
        ],
        "labelOutboundReasons": [
            {"id": reason_id, "name": reason_name}
            for reason_id, reason_name in LABEL_OUTBOUND_REASONS.items()
        ],
        "receipts": receipts[:10],
        "labels": inventory_labels[:80],
        "labelStats": {
            "inStock": len([label for label in inventory_labels if label["status"] == "in_stock"]),
            "outbound": len([label for label in inventory_labels if label["status"] == "outbound"]),
            "pendingReceipts": len([receipt for receipt in receipts if receipt["status"] == "inspected"]),
        },
        "capabilities": [
            "到货核检",
            "新旧品判断",
            "单件二维码标签",
            "扫码入库",
            "扫码出库剪标",
        ],
    }


def build_inventory_alerts() -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []

    for product in products:
        if available_stock(product) <= product.get("safeStock", 0):
            alerts.append(
                {
                    "level": "warning",
                    "title": "库存下限预警",
                    "message": f"{product['name']} 可用库存 {available_stock(product)}，已低于安全库存 {product.get('safeStock', 0)}",
                }
            )

        expiry_date = product.get("expiryDate")
        if expiry_date:
            try:
                expiry = datetime.fromisoformat(expiry_date)
                days_left = (expiry - datetime.now()).days
                if days_left <= 30:
                    alerts.append(
                        {
                            "level": "warning",
                            "title": "效期临期预警",
                            "message": f"{product['name']} 距离效期仅剩 {max(days_left, 0)} 天",
                        }
                    )
            except ValueError:
                pass

    if not alerts:
        alerts.append(
            {
                "level": "normal",
                "title": "库存同步正常",
                "message": "全部渠道库存镜像与中央库存保持一致",
            }
        )

    return alerts


def record_stock_movement(
    *,
    movement_type: str,
    sku_id: str,
    quantity: int,
    operator: str,
    scene: str,
    before_stock: int,
    after_stock: int,
    warehouse: str,
    location: str,
    channel: str | None = None,
    reference_no: str | None = None,
    remark: str | None = None,
) -> None:
    product = find_product(sku_id)
    stock_movements.insert(
        0,
        {
            "movementId": str(uuid4()),
            "type": movement_type,
            "scene": scene,
            "skuId": sku_id,
            "productName": product["name"] if product else sku_id,
            "quantity": quantity,
            "beforeStock": before_stock,
            "afterStock": after_stock,
            "warehouse": warehouse,
            "location": location,
            "channel": channel or "",
            "referenceNo": reference_no or "",
            "operator": operator,
            "remark": remark or "",
            "createdAt": utc_now(),
        },
    )


def generate_sku_id(name: str) -> str:
    prefix = "".join(ch for ch in name.upper() if ch.isalnum())[:3] or "SKU"
    return f"{prefix}-{random.randint(1000, 9999)}"


def generate_barcode() -> str:
    return f"69{random.randint(10**10, 10**11 - 1)}"
