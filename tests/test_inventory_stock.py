import copy
import unittest

from backend import services


class InventoryStockTests(unittest.TestCase):
    def setUp(self):
        self.original_state = {
            "products": copy.deepcopy(services.products),
            "orders": copy.deepcopy(services.orders),
            "stock_events": copy.deepcopy(services.stock_events),
            "stock_movements": copy.deepcopy(services.stock_movements),
            "receipts": copy.deepcopy(services.receipts),
            "inventory_labels": copy.deepcopy(services.inventory_labels),
        }
        self.original_persist_state = services.persist_state
        services.persist_state = lambda: None

    def tearDown(self):
        services.products[:] = self.original_state["products"]
        services.orders[:] = self.original_state["orders"]
        services.stock_events[:] = self.original_state["stock_events"]
        services.stock_movements[:] = self.original_state["stock_movements"]
        services.receipts[:] = self.original_state["receipts"]
        services.inventory_labels[:] = self.original_state["inventory_labels"]
        services.persist_state = self.original_persist_state

    def test_minor_flaw_labels_count_toward_total_inventory(self):
        self.seed_product_with_stale_stock()

        system = services.get_inventory_system()
        product = services.list_products()[0]
        dashboard = services.get_dashboard()

        self.assertEqual(system["engine"]["totalStock"], 3)
        self.assertEqual(system["labelStats"]["minorFlaw"], 2)
        self.assertEqual(product["availableStock"], 3)
        self.assertEqual(dashboard["metrics"]["totalInventory"], 3)

    def test_outbound_minor_flaw_label_uses_effective_stock(self):
        services.products[:] = [
            {
                "skuId": "SKU-TEST",
                "name": "Test Pot",
                "centralStock": 0,
                "lockedStock": 0,
                "safeStock": 0,
                "warehouse": "Main",
                "location": "A-01",
            }
        ]
        services.inventory_labels[:] = [
            {
                "labelCode": "0001-001",
                "skuId": "SKU-TEST",
                "productName": "Test Pot",
                "status": "in_stock",
                "qualityGrade": "minor_flaw",
                "qualityGradeName": "Minor flaw",
            }
        ]
        services.orders[:] = []
        services.stock_events[:] = []
        services.stock_movements[:] = []
        services.receipts[:] = []

        result = services.outbound_by_label(
            label_code="0001-001",
            reason_id="offline",
            operator="Tester",
        )

        self.assertEqual(result["label"]["status"], "outbound")
        self.assertEqual(result["product"]["availableStock"], 0)
        self.assertEqual(services.products[0]["centralStock"], 0)

    def seed_product_with_stale_stock(self):
        services.products[:] = [
            {
                "skuId": "SKU-TEST",
                "name": "Test Pot",
                "centralStock": 2,
                "lockedStock": 0,
                "safeStock": 0,
                "warehouse": "Main",
            }
        ]
        services.inventory_labels[:] = [
            {
                "labelCode": "0001-001",
                "skuId": "SKU-TEST",
                "productName": "Test Pot",
                "status": "in_stock",
                "qualityGrade": "perfect",
                "qualityGradeName": "Perfect",
            },
            {
                "labelCode": "0001-002",
                "skuId": "SKU-TEST",
                "productName": "Test Pot",
                "status": "in_stock",
                "qualityGrade": "minor_flaw",
                "qualityGradeName": "Minor flaw",
            },
            {
                "labelCode": "0001-003",
                "skuId": "SKU-TEST",
                "productName": "Test Pot",
                "status": "in_stock",
                "qualityGrade": "minor_flaw",
                "qualityGradeName": "Minor flaw",
            },
        ]
        services.orders[:] = []
        services.stock_events[:] = []
        services.stock_movements[:] = []
        services.receipts[:] = []


if __name__ == "__main__":
    unittest.main()
