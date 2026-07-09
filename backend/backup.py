import os
import re
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .storage import DB_PATH, ROOT, ensure_database


BACKUP_DIR = ROOT / "backups"
DEFAULT_BACKUP_INTERVAL_SECONDS = 24 * 60 * 60
DEFAULT_BACKUP_RETENTION_COUNT = 30

_backup_lock = threading.Lock()
_scheduler_stop = threading.Event()
_scheduler_thread: threading.Thread | None = None
_scheduler_state: dict[str, Any] = {
    "running": False,
    "intervalSeconds": DEFAULT_BACKUP_INTERVAL_SECONDS,
    "retentionCount": DEFAULT_BACKUP_RETENTION_COUNT,
    "lastRunAt": None,
    "nextRunAt": None,
    "lastError": None,
}


def create_database_backup(reason: str = "manual") -> dict[str, Any]:
    ensure_database()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    safe_reason = normalize_reason(reason)
    created_at = datetime.now()
    filename = f"inventory_{created_at.strftime('%Y%m%d_%H%M%S')}_{safe_reason}.sqlite"
    backup_path = unique_backup_path(BACKUP_DIR / filename)

    with _backup_lock:
        with sqlite3.connect(DB_PATH) as source:
            with sqlite3.connect(backup_path) as target:
                source.backup(target)

    cleanup_old_backups(get_retention_count())
    return backup_metadata(backup_path)


def list_database_backups() -> list[dict[str, Any]]:
    if not BACKUP_DIR.exists():
        return []
    return [
        backup_metadata(path)
        for path in sorted(BACKUP_DIR.glob("inventory_*.sqlite"), key=lambda item: item.stat().st_mtime, reverse=True)
    ]


def get_backup_status() -> dict[str, Any]:
    latest_backup = next(iter(list_database_backups()), None)
    return {
        **_scheduler_state,
        "backupDir": str(BACKUP_DIR),
        "databasePath": str(DB_PATH),
        "latestBackup": latest_backup,
    }


def start_backup_scheduler() -> None:
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        return

    interval_seconds = get_interval_seconds()
    retention_count = get_retention_count()
    _scheduler_stop.clear()
    _scheduler_state.update(
        {
            "running": True,
            "intervalSeconds": interval_seconds,
            "retentionCount": retention_count,
            "lastError": None,
        }
    )
    update_next_run(interval_seconds)

    _scheduler_thread = threading.Thread(
        target=run_scheduler,
        args=(interval_seconds,),
        name="inventory-backup-scheduler",
        daemon=True,
    )
    _scheduler_thread.start()


def stop_backup_scheduler() -> None:
    _scheduler_stop.set()
    if _scheduler_thread and _scheduler_thread.is_alive():
        _scheduler_thread.join(timeout=3)
    _scheduler_state["running"] = False
    _scheduler_state["nextRunAt"] = None


def run_scheduler(interval_seconds: int) -> None:
    while not _scheduler_stop.wait(interval_seconds):
        try:
            create_database_backup("auto")
            _scheduler_state["lastRunAt"] = datetime.now().isoformat(timespec="seconds")
            _scheduler_state["lastError"] = None
        except Exception as error:  # pragma: no cover - scheduler errors are surfaced via status API.
            _scheduler_state["lastError"] = str(error)
        finally:
            update_next_run(interval_seconds)


def update_next_run(interval_seconds: int) -> None:
    _scheduler_state["nextRunAt"] = (
        datetime.now() + timedelta(seconds=interval_seconds)
    ).isoformat(timespec="seconds")


def cleanup_old_backups(retention_count: int) -> None:
    if retention_count <= 0 or not BACKUP_DIR.exists():
        return

    backups = sorted(
        BACKUP_DIR.glob("inventory_*.sqlite"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    for path in backups[retention_count:]:
        path.unlink(missing_ok=True)


def backup_metadata(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "filename": path.name,
        "path": str(path),
        "size": stat.st_size,
        "createdAt": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def unique_backup_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    index = 1
    while True:
        candidate = path.with_name(f"{stem}_{index}{suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def normalize_reason(reason: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", reason.strip().lower()).strip("-")
    return normalized or "manual"


def get_interval_seconds() -> int:
    return get_positive_int_env("INVENTORY_BACKUP_INTERVAL_SECONDS", DEFAULT_BACKUP_INTERVAL_SECONDS)


def get_retention_count() -> int:
    return get_positive_int_env("INVENTORY_BACKUP_RETENTION_COUNT", DEFAULT_BACKUP_RETENTION_COUNT)


def get_positive_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default
