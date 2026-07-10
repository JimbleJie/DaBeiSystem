import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "inventory.sqlite"
STATE_KEY = "inventory_state"

ENTITY_TABLES = (
    "products",
    "orders",
    "stock_events",
    "stock_movements",
    "receipts",
    "inventory_labels",
)


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_database() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS products (
                sku_id TEXT PRIMARY KEY,
                product_id TEXT,
                name TEXT NOT NULL,
                category TEXT,
                central_stock INTEGER NOT NULL DEFAULT 0,
                locked_stock INTEGER NOT NULL DEFAULT 0,
                safe_stock INTEGER NOT NULL DEFAULT 0,
                barcode TEXT,
                warehouse TEXT,
                location TEXT,
                created_at TEXT,
                updated_at TEXT,
                sort_order INTEGER NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS inventory_labels (
                label_code TEXT PRIMARY KEY,
                sku_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                status TEXT NOT NULL,
                receipt_id TEXT,
                inbound_at TEXT,
                outbound_at TEXT,
                outbound_reason TEXT,
                operator TEXT,
                sort_order INTEGER NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS receipts (
                receipt_id TEXT PRIMARY KEY,
                sku_id TEXT,
                product_name TEXT NOT NULL,
                status TEXT NOT NULL,
                qualified_quantity INTEGER NOT NULL DEFAULT 0,
                operator TEXT,
                created_at TEXT,
                inbound_at TEXT,
                sort_order INTEGER NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                platform_order_id TEXT,
                platform_id TEXT NOT NULL,
                sku_id TEXT NOT NULL,
                product_name TEXT,
                quantity INTEGER NOT NULL DEFAULT 0,
                amount REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                logistics_status TEXT,
                created_at TEXT,
                updated_at TEXT,
                sort_order INTEGER NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS stock_movements (
                movement_id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                sku_id TEXT,
                product_name TEXT,
                quantity INTEGER NOT NULL DEFAULT 0,
                before_stock INTEGER NOT NULL DEFAULT 0,
                after_stock INTEGER NOT NULL DEFAULT 0,
                warehouse TEXT,
                location TEXT,
                created_at TEXT,
                sort_order INTEGER NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS stock_events (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                sku_id TEXT,
                quantity INTEGER NOT NULL DEFAULT 0,
                message TEXT,
                created_at TEXT,
                sort_order INTEGER NOT NULL,
                payload TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_products_sort ON products(sort_order);
            CREATE INDEX IF NOT EXISTS idx_inventory_labels_sku ON inventory_labels(sku_id);
            CREATE INDEX IF NOT EXISTS idx_inventory_labels_status ON inventory_labels(status);
            CREATE INDEX IF NOT EXISTS idx_inventory_labels_sort ON inventory_labels(sort_order);
            CREATE INDEX IF NOT EXISTS idx_receipts_sort ON receipts(sort_order);
            CREATE INDEX IF NOT EXISTS idx_orders_sort ON orders(sort_order);
            CREATE INDEX IF NOT EXISTS idx_stock_movements_sort ON stock_movements(sort_order);
            CREATE INDEX IF NOT EXISTS idx_stock_events_sort ON stock_events(sort_order);
            """
        )


def load_state() -> dict[str, Any]:
    ensure_database()
    with connect() as connection:
        migrate_legacy_snapshot(connection)
        return {
            "products": read_payloads(connection, "products"),
            "orders": read_payloads(connection, "orders"),
            "stockEvents": read_payloads(connection, "stock_events"),
            "stockMovements": read_payloads(connection, "stock_movements"),
            "receipts": read_payloads(connection, "receipts"),
            "inventoryLabels": read_payloads(connection, "inventory_labels"),
        }


def load_json_state(key: str, default: Any = None) -> Any:
    ensure_database()
    with connect() as connection:
        row = connection.execute(
            "SELECT value FROM app_state WHERE key = ?",
            (key,),
        ).fetchone()
    if row is None:
        return default
    try:
        return json.loads(row["value"])
    except json.JSONDecodeError:
        return default


def save_json_state(key: str, value: Any) -> None:
    ensure_database()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO app_state (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, json.dumps(value, ensure_ascii=False, separators=(",", ":"))),
        )


def delete_state(key: str) -> None:
    ensure_database()
    with connect() as connection:
        connection.execute(
            "DELETE FROM app_state WHERE key = ?",
            (key,),
        )


def save_state(state: dict[str, Any]) -> None:
    ensure_database()
    with connect() as connection:
        write_state(connection, state)


def migrate_legacy_snapshot(connection: sqlite3.Connection) -> None:
    if has_modeled_data(connection):
        return

    row = connection.execute(
        "SELECT value FROM app_state WHERE key = ?",
        (STATE_KEY,),
    ).fetchone()
    if row is None:
        return

    state = json.loads(row["value"])
    write_state(connection, state)
    connection.execute(
        "INSERT OR IGNORE INTO schema_migrations (version) VALUES (1)"
    )


def has_modeled_data(connection: sqlite3.Connection) -> bool:
    for table in ENTITY_TABLES:
        count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if count:
            return True
    return False


def read_payloads(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        f"SELECT payload FROM {table} ORDER BY sort_order ASC"
    ).fetchall()
    return [json.loads(row["payload"]) for row in rows]


def write_state(connection: sqlite3.Connection, state: dict[str, Any]) -> None:
    for table in ENTITY_TABLES:
        connection.execute(f"DELETE FROM {table}")

    insert_products(connection, state.get("products", []))
    insert_orders(connection, state.get("orders", []))
    insert_stock_events(connection, state.get("stockEvents", []))
    insert_stock_movements(connection, state.get("stockMovements", []))
    insert_receipts(connection, state.get("receipts", []))
    insert_inventory_labels(connection, state.get("inventoryLabels", []))


def dumps(item: dict[str, Any]) -> str:
    return json.dumps(item, ensure_ascii=False, separators=(",", ":"))


def insert_products(connection: sqlite3.Connection, items: list[dict[str, Any]]) -> None:
    connection.executemany(
        """
        INSERT INTO products (
            sku_id, product_id, name, category, central_stock, locked_stock,
            safe_stock, barcode, warehouse, location, created_at, updated_at,
            sort_order, payload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["skuId"],
                item.get("productId", ""),
                item.get("name", ""),
                item.get("category", ""),
                int(item.get("centralStock") or 0),
                int(item.get("lockedStock") or 0),
                int(item.get("safeStock") or 0),
                item.get("barcode", ""),
                item.get("warehouse", ""),
                item.get("location", ""),
                item.get("createdAt", ""),
                item.get("updatedAt", ""),
                index,
                dumps(item),
            )
            for index, item in enumerate(items)
        ],
    )


def insert_inventory_labels(connection: sqlite3.Connection, items: list[dict[str, Any]]) -> None:
    connection.executemany(
        """
        INSERT INTO inventory_labels (
            label_code, sku_id, product_name, status, receipt_id, inbound_at,
            outbound_at, outbound_reason, operator, sort_order, payload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["labelCode"],
                item.get("skuId", ""),
                item.get("productName", ""),
                item.get("status", ""),
                item.get("receiptId", ""),
                item.get("inboundAt", ""),
                item.get("outboundAt", ""),
                item.get("outboundReason", ""),
                item.get("operator", ""),
                index,
                dumps(item),
            )
            for index, item in enumerate(items)
        ],
    )


def insert_receipts(connection: sqlite3.Connection, items: list[dict[str, Any]]) -> None:
    connection.executemany(
        """
        INSERT INTO receipts (
            receipt_id, sku_id, product_name, status, qualified_quantity,
            operator, created_at, inbound_at, sort_order, payload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["receiptId"],
                item.get("skuId", ""),
                item.get("productName", ""),
                item.get("status", ""),
                int(item.get("qualifiedQuantity") or 0),
                item.get("operator") or item.get("inspector", ""),
                item.get("createdAt", ""),
                item.get("inboundAt", ""),
                index,
                dumps(item),
            )
            for index, item in enumerate(items)
        ],
    )


def insert_orders(connection: sqlite3.Connection, items: list[dict[str, Any]]) -> None:
    connection.executemany(
        """
        INSERT INTO orders (
            order_id, platform_order_id, platform_id, sku_id, product_name,
            quantity, amount, status, logistics_status, created_at, updated_at,
            sort_order, payload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["orderId"],
                item.get("platformOrderId", ""),
                item.get("platformId", ""),
                item.get("skuId", ""),
                item.get("productName", ""),
                int(item.get("quantity") or 0),
                float(item.get("amount") or 0),
                item.get("status", ""),
                item.get("logisticsStatus", ""),
                item.get("createdAt", ""),
                item.get("updatedAt", ""),
                index,
                dumps(item),
            )
            for index, item in enumerate(items)
        ],
    )


def insert_stock_movements(connection: sqlite3.Connection, items: list[dict[str, Any]]) -> None:
    connection.executemany(
        """
        INSERT INTO stock_movements (
            movement_id, type, sku_id, product_name, quantity, before_stock,
            after_stock, warehouse, location, created_at, sort_order, payload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["movementId"],
                item.get("type", ""),
                item.get("skuId", ""),
                item.get("productName", ""),
                int(item.get("quantity") or 0),
                int(item.get("beforeStock") or 0),
                int(item.get("afterStock") or 0),
                item.get("warehouse", ""),
                item.get("location", ""),
                item.get("createdAt", ""),
                index,
                dumps(item),
            )
            for index, item in enumerate(items)
        ],
    )


def insert_stock_events(connection: sqlite3.Connection, items: list[dict[str, Any]]) -> None:
    connection.executemany(
        """
        INSERT INTO stock_events (
            id, type, sku_id, quantity, message, created_at, sort_order, payload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item["id"],
                item.get("type", ""),
                item.get("skuId", ""),
                int(item.get("quantity") or 0),
                item.get("message", ""),
                item.get("createdAt", ""),
                index,
                dumps(item),
            )
            for index, item in enumerate(items)
        ],
    )
