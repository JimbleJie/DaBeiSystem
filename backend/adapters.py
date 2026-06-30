import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def random_buyer() -> str:
    return random.choice(["王女士", "陈先生", "刘女士", "赵先生", "林女士", "黄先生"])


@dataclass(frozen=True)
class Platform:
    id: str
    name: str
    color: str


class MockPlatformAdapter:
    def __init__(self, platform: Platform) -> None:
        self.platform = platform

    async def pull_orders(self, products: list[dict[str, Any]]) -> list[dict[str, Any]]:
        product = random.choice(products)
        quantity = random.randint(1, 2)

        return [
            {
                "platformOrderId": f"{self.platform.id.upper()}-{int(time.time() * 1000)}",
                "platformId": self.platform.id,
                "skuId": product["skuId"],
                "quantity": quantity,
                "buyer": random_buyer(),
                "status": "paid",
            }
        ]

    async def sync_inventory(self, product: dict[str, Any]) -> dict[str, Any]:
        return {
            "platformId": self.platform.id,
            "skuId": product["skuId"],
            "availableStock": max(product["centralStock"] - product["lockedStock"], 0),
            "syncedAt": utc_now(),
        }

    async def get_logistics(self, order: dict[str, Any]) -> list[dict[str, str]]:
        events = [
            {
                "status": "订单创建",
                "description": f"{order['platformOrderId']} 已同步到订单中心",
                "time": order["createdAt"],
            }
        ]

        if order["status"] == "paid":
            events.append(
                {
                    "status": "等待发货",
                    "description": "订单已支付，等待仓库出库",
                    "time": order["updatedAt"],
                }
            )

        if order["status"] == "shipped":
            events.extend(
                [
                    {
                        "status": "已揽收",
                        "description": f"快递单号 {order['trackingNo']}",
                        "time": order["updatedAt"],
                    },
                    {
                        "status": "运输中",
                        "description": "包裹正在发往目的地分拨中心",
                        "time": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
                    },
                ]
            )

        return events


PLATFORMS = [
    Platform(id="taobao", name="淘宝", color="#e6582f"),
    Platform(id="douyin", name="抖音", color="#16191f"),
    Platform(id="xiaohongshu", name="小红书", color="#c92f43"),
    Platform(id="wechat", name="微信电商", color="#218a4f"),
    Platform(id="private_domain", name="私域渠道", color="#6d5bd0"),
]

ADAPTERS = {platform.id: MockPlatformAdapter(platform) for platform in PLATFORMS}
