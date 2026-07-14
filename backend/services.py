import random
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from .adapters import ADAPTERS, PLATFORMS, random_buyer, utc_now
from .storage import load_json_state, load_state, save_json_state, save_state


class BusinessError(Exception):
    pass


def _initial_products() -> list[dict[str, Any]]:
    return []


products = _initial_products()
orders: list[dict[str, Any]] = []
stock_events: list[dict[str, Any]] = []
stock_movements: list[dict[str, Any]] = []
receipts: list[dict[str, Any]] = []
inventory_labels: list[dict[str, Any]] = []

SHORT_LABEL_CODE_PATTERN = re.compile(r"^\d{4}-\d{3}$")
LEGACY_RECEIPT_LABEL_PATTERN = re.compile(r"^QR-RCV-\d{14}-(\d+)-(\d{3})$")
PERSONNEL_STATE_KEY = "personnel"
DEFAULT_PERSONNEL_NAMES = ("小梅雨", "六一")
QUALITY_GRADE_NAMES = {
    "perfect": "完品",
    "minor_flaw": "微瑕",
}


def export_state() -> dict[str, Any]:
    return {
        "products": products,
        "orders": orders,
        "stockEvents": stock_events,
        "stockMovements": stock_movements,
        "receipts": receipts,
        "inventoryLabels": inventory_labels,
    }


def load_persisted_state() -> None:
    state = load_state()
    if state is None:
        return

    products[:] = state.get("products", [])
    orders[:] = state.get("orders", [])
    stock_events[:] = state.get("stockEvents", [])
    stock_movements[:] = state.get("stockMovements", [])
    receipts[:] = state.get("receipts", [])
    inventory_labels[:] = state.get("inventoryLabels", [])
    migrated = migrate_label_codes_to_short()
    if normalize_existing_quality_grades():
        migrated = True
    if migrated:
        persist_state()


def persist_state() -> None:
    save_state(export_state())


def normalize_quality_grade(value: str | None) -> tuple[str, str]:
    grade = str(value or "perfect").strip()
    if grade not in QUALITY_GRADE_NAMES:
        raise BusinessError("请选择完品或微瑕")
    return grade, QUALITY_GRADE_NAMES[grade]


def apply_quality_defaults(item: dict[str, Any]) -> bool:
    changed = False
    grade = item.get("qualityGrade") or "perfect"
    if grade not in QUALITY_GRADE_NAMES:
        grade = "perfect"
    grade_name = QUALITY_GRADE_NAMES[grade]
    if item.get("qualityGrade") != grade:
        item["qualityGrade"] = grade
        changed = True
    if item.get("qualityGradeName") != grade_name:
        item["qualityGradeName"] = grade_name
        changed = True
    return changed


def normalize_existing_quality_grades() -> bool:
    changed = False
    for label in inventory_labels:
        changed = apply_quality_defaults(label) or changed
    for receipt in receipts:
        changed = apply_quality_defaults(receipt) or changed
    return changed


def normalize_person_name(name: str | None) -> str:
    return str(name or "").strip()


def build_personnel_item(name: str) -> dict[str, str]:
    return {
        "id": f"person-{uuid4().hex[:10]}",
        "name": name,
    }


def get_personnel() -> list[dict[str, str]]:
    saved = load_json_state(PERSONNEL_STATE_KEY, None)
    saved_items = saved.get("items") if isinstance(saved, dict) else saved
    if isinstance(saved_items, list):
        personnel: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in saved_items:
            if isinstance(item, dict):
                name = normalize_person_name(item.get("name"))
                person_id = str(item.get("id") or f"person-{uuid4().hex[:10]}")
            else:
                name = normalize_person_name(item)
                person_id = f"person-{uuid4().hex[:10]}"
            if not name or name in seen:
                continue
            seen.add(name)
            personnel.append({"id": person_id, "name": name})
        if personnel:
            return personnel

    personnel = [build_personnel_item(name) for name in DEFAULT_PERSONNEL_NAMES]
    save_personnel(personnel)
    return personnel


def save_personnel(personnel: list[dict[str, str]]) -> None:
    save_json_state(PERSONNEL_STATE_KEY, {"items": personnel})


def list_personnel() -> list[dict[str, str]]:
    return get_personnel()


def create_personnel(name: str) -> dict[str, str]:
    normalized_name = normalize_person_name(name)
    if not normalized_name:
        raise BusinessError("人员姓名不能为空")

    personnel = get_personnel()
    if any(item["name"] == normalized_name for item in personnel):
        raise BusinessError("人员已存在")

    person = build_personnel_item(normalized_name)
    personnel.append(person)
    save_personnel(personnel)
    return person


def delete_personnel(person_id: str) -> dict[str, str]:
    personnel = get_personnel()
    if len(personnel) <= 1:
        raise BusinessError("至少保留一名人员")

    next_personnel = [item for item in personnel if item["id"] != person_id]
    if len(next_personnel) == len(personnel):
        raise BusinessError("人员不存在")

    removed = next(item for item in personnel if item["id"] == person_id)
    save_personnel(next_personnel)
    return removed

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


def is_short_label_code(value: str) -> bool:
    return bool(SHORT_LABEL_CODE_PATTERN.match(value or ""))


def receipt_label_prefix(receipt_id: str) -> int:
    numeric_groups = re.findall(r"\d+", receipt_id or "")
    if not numeric_groups:
        return 0
    return int(numeric_groups[-1]) % 10000


def label_sequence_from_code(label_code: str, fallback_index: int) -> int:
    legacy_match = LEGACY_RECEIPT_LABEL_PATTERN.match(label_code or "")
    if legacy_match:
        return int(legacy_match.group(2))
    if is_short_label_code(label_code):
        return int(label_code[-3:])
    numeric_groups = re.findall(r"\d+", label_code or "")
    if numeric_groups:
        return max(int(numeric_groups[-1]) % 1000, 1)
    return fallback_index + 1


def build_short_label_code(prefix: int, sequence: int) -> str:
    return f"{prefix % 10000:04d}-{max(sequence, 1) % 1000:03d}"


def resolve_receipt_label_prefix(receipt_id: str, label_codes: list[str], used_codes: set[str]) -> int:
    base_prefix = receipt_label_prefix(receipt_id)
    sequences = [
        label_sequence_from_code(label_code, index)
        for index, label_code in enumerate(label_codes)
        if not is_short_label_code(label_code)
    ]
    if not sequences:
        return base_prefix

    for offset in range(10000):
        candidate_prefix = (base_prefix + offset) % 10000
        candidate_codes = {
            build_short_label_code(candidate_prefix, sequence)
            for sequence in sequences
        }
        if candidate_codes.isdisjoint(used_codes):
            return candidate_prefix
    raise BusinessError("短标签编码已用尽")


def generate_short_label_codes(receipt_id: str, quantity: int) -> list[str]:
    used_codes = {label.get("labelCode", "") for label in inventory_labels}
    base_prefix = receipt_label_prefix(receipt_id)
    for offset in range(10000):
        prefix = (base_prefix + offset) % 10000
        codes = [build_short_label_code(prefix, index + 1) for index in range(quantity)]
        if all(code not in used_codes for code in codes):
            return codes
    raise BusinessError("短标签编码已用尽")


def migrate_label_codes_to_short() -> bool:
    changed = False
    code_map: dict[str, str] = {}
    labels_by_code = {label.get("labelCode", ""): label for label in inventory_labels}
    used_codes = {
        label["labelCode"]
        for label in inventory_labels
        if is_short_label_code(label.get("labelCode", ""))
    }

    for receipt in receipts:
        label_codes = receipt.get("labelCodes")
        if not isinstance(label_codes, list):
            continue

        prefix = resolve_receipt_label_prefix(receipt.get("receiptId", ""), label_codes, used_codes)
        next_label_codes: list[str] = []
        for index, old_code in enumerate(label_codes):
            if is_short_label_code(old_code):
                next_label_codes.append(old_code)
                used_codes.add(old_code)
                continue

            new_code = build_short_label_code(prefix, label_sequence_from_code(old_code, index))
            code_map[old_code] = new_code
            next_label_codes.append(new_code)
            used_codes.add(new_code)

            label = labels_by_code.get(old_code)
            if label is not None:
                label["legacyLabelCode"] = old_code
                label["labelCode"] = new_code
                changed = True

        if next_label_codes != label_codes:
            receipt["labelCodes"] = next_label_codes
            changed = True

    used_codes.update(code_map.values())
    for index, label in enumerate(inventory_labels):
        old_code = label.get("labelCode", "")
        if is_short_label_code(old_code):
            continue

        base_prefix = receipt_label_prefix(label.get("receiptId", "")) or (index + 1)
        sequence = label_sequence_from_code(old_code, index)
        for offset in range(10000):
            new_code = build_short_label_code(base_prefix + offset, sequence)
            if new_code not in used_codes:
                break
        else:
            raise BusinessError("短标签编码已用尽")

        label["legacyLabelCode"] = old_code
        label["labelCode"] = new_code
        code_map[old_code] = new_code
        used_codes.add(new_code)
        changed = True

    if code_map:
        for movement in stock_movements:
            reference_no = movement.get("referenceNo")
            if reference_no in code_map:
                movement["referenceNo"] = code_map[reference_no]
                changed = True

    return changed


load_persisted_state()


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
        "personnel": list_personnel(),
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

    persist_state()
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
    products.insert(0, product)

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

    persist_state()
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
    persist_state()
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
    persist_state()
    return serialize_product(product)


def delete_inventory_label(label_code: str) -> dict[str, Any]:
    label = find_label(label_code)
    if label is None:
        raise BusinessError("二维码标签不存在")
    actual_label_code = label["labelCode"]

    product = find_product(label.get("skuId", ""))
    before_stock = product["centralStock"] if product else 0
    if product is not None and label.get("status") == "in_stock":
        product["centralStock"] = max(product["centralStock"] - 1, 0)
        product["updatedAt"] = utc_now()

    inventory_labels.remove(label)

    for receipt in receipts:
        label_codes = receipt.get("labelCodes")
        if isinstance(label_codes, list) and actual_label_code in label_codes:
            label_codes.remove(actual_label_code)

    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "delete_label",
            "message": f"二维码标签 {actual_label_code} 已删除",
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
            reference_no=actual_label_code,
        )

    persist_state()
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

    persist_state()
    return serialize_product(product)


def inspect_receipt(*, product_name: str, qualified_quantity: int, inspector: str | None = None) -> dict[str, Any]:
    receipt = {
        "receiptId": f"RCV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
        "productName": product_name,
        "qualifiedQuantity": qualified_quantity,
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
            "message": f"{product_name} 到货核检完成：合格 {qualified_quantity} 个",
            "createdAt": utc_now(),
        },
    )
    persist_state()
    return receipt


def inbound_with_labels(
    *,
    receipt_id: str,
    product_mode: str,
    sku_id: str | None,
    product_name: str | None,
    operator: str | None = None,
    quality_grade: str | None = None,
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

    grade, grade_name = normalize_quality_grade(quality_grade)
    quantity = receipt["qualifiedQuantity"]
    before_stock = product["centralStock"]
    product["centralStock"] += quantity
    product["updatedAt"] = utc_now()
    labels = []
    label_codes = generate_short_label_codes(receipt_id, quantity)

    for index in range(quantity):
        label = {
            "labelCode": label_codes[index],
            "skuId": product["skuId"],
            "productName": product["name"],
            "status": "in_stock",
            "receiptId": receipt_id,
            "printedAt": utc_now(),
            "inboundAt": utc_now(),
            "outboundAt": "",
            "outboundReason": "",
            "qualityGrade": grade,
            "qualityGradeName": grade_name,
            "operator": operator or "入库员",
        }
        labels.append(label)
        inventory_labels.insert(0, label)

    receipt["status"] = "inbound"
    receipt["skuId"] = product["skuId"]
    receipt["productName"] = product["name"]
    receipt["operator"] = operator or "入库员"
    receipt["qualityGrade"] = grade
    receipt["qualityGradeName"] = grade_name
    receipt["labelCodes"] = [label["labelCode"] for label in labels]
    receipt["inboundAt"] = utc_now()

    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "label_inbound",
            "message": f"{product['name']} {grade_name} 打印并绑定 {quantity} 个二维码标签，扫码入库完成",
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
        remark=f"每个{grade_name}已贴二维码标签",
    )

    persist_state()
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

    persist_state()
    return {
        "label": label,
        "product": serialize_product(product),
        "movement": stock_movements[0],
    }


def reinbound_by_label(*, label_code: str, operator: str | None = None, remark: str | None = None) -> dict[str, Any]:
    label = find_label(label_code)
    if label is None:
        raise BusinessError("二维码标签不存在")
    if label.get("status") != "outbound":
        raise BusinessError("该标签未出库，无需重新入库")

    product = find_product(label.get("skuId", ""))
    if product is None:
        raise BusinessError("标签对应商品不存在")

    before_stock = product["centralStock"]
    product["centralStock"] += 1
    product["updatedAt"] = utc_now()
    label["status"] = "in_stock"
    label["outboundAt"] = ""
    label["outboundReason"] = ""
    label["reInboundAt"] = utc_now()
    label["operator"] = operator or "入库员"

    stock_events.insert(
        0,
        {
            "id": str(uuid4()),
            "type": "label_reinbound",
            "message": f"标签 {label['labelCode']} 重新入库，{product['name']} 库存加回 1 个",
            "skuId": product["skuId"],
            "quantity": 1,
            "createdAt": utc_now(),
        },
    )
    record_stock_movement(
        movement_type="re_inbound",
        sku_id=product["skuId"],
        quantity=1,
        operator=operator or "入库员",
        scene="出库标签重新入库",
        before_stock=before_stock,
        after_stock=product["centralStock"],
        warehouse=product.get("warehouse", "主仓"),
        location=product.get("location", ""),
        reference_no=label["labelCode"],
        remark=remark or "清除原出库状态并恢复在库",
    )

    persist_state()
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

    persist_state()
    return {
        "outboundNo": outbound_no,
        "product": serialize_product(product),
        "movement": stock_movements[0],
    }


async def pull_platform_orders(platform_id: str | None = None) -> dict[str, Any]:
    if not products:
        raise BusinessError("暂无商品，无法拉取订单")

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

    persist_state()
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


def reset_system_data() -> dict[str, Any]:
    products.clear()
    products.extend(_initial_products())
    orders.clear()
    stock_events.clear()
    stock_movements.clear()
    receipts.clear()
    inventory_labels.clear()
    persist_state()
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
    return next(
        (
            label for label in inventory_labels
            if label["labelCode"] == label_code or label.get("legacyLabelCode") == label_code
        ),
        None,
    )


def get_print_label(label_code: str) -> dict[str, str]:
    label = find_label(label_code)
    if label is None:
        raise BusinessError("标签不存在")
    return {
        "labelCode": label["labelCode"],
        "productName": label["productName"],
    }


def list_print_labels_for_sku(sku_id: str) -> list[dict[str, str]]:
    product = find_product(sku_id)
    if product is None:
        raise BusinessError("商品不存在")

    labels = [
        {
            "labelCode": label["labelCode"],
            "productName": label["productName"],
        }
        for label in inventory_labels
        if label["skuId"] == sku_id
    ]
    if not labels:
        raise BusinessError("暂无可打印标签")
    return labels


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
    normalize_existing_quality_grades()
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
        "personnel": list_personnel(),
        "receipts": receipts[:10],
        "labels": inventory_labels[:80],
        "labelStats": {
            "inStock": len([label for label in inventory_labels if label["status"] == "in_stock"]),
            "outbound": len([label for label in inventory_labels if label["status"] == "outbound"]),
            "minorFlaw": len([
                label for label in inventory_labels
                if label.get("qualityGrade") == "minor_flaw" and label.get("status") == "in_stock"
            ]),
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
