
import unittest
import tempfile
from pathlib import Path

from supplydesk.service import OrderService


class AdditionalTests(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.service = OrderService(
            Path(self.directory.name) / "state.json"
        )

    # Test 1: Normal behavior
    def test_regular_customer_quote(self):
        quote = self.service.quote(
            "regular",
            [{"product_id": "notebook", "quantity": 1}]
        )
        self.assertEqual(quote["subtotal_cents"], 500)
        self.assertEqual(quote["total_cents"], 500)

    # Test 2: Boundary behavior
    def test_zero_quantity(self):
        with self.assertRaises(ValueError):
            self.service.quote(
                "regular",
                [{"product_id": "notebook", "quantity": 0}]
            )

    # Test 3: Invalid input
    def test_invalid_customer_type(self):
        with self.assertRaises(ValueError):
            self.service.quote(
                "unknown",
                [{"product_id": "notebook", "quantity": 1}]
            )

    # Test 4: Behavior to preserve
    def test_quote_does_not_change_stock(self):
        before = self.service.catalog()

        self.service.quote(
            "regular",
            [{"product_id": "notebook", "quantity": 1}]
        )

        after = self.service.catalog()
        self.assertEqual(before, after)

    # Test 5: Express delivery costs $12
    def test_express_delivery_fee(self):
        quote = self.service.quote(
            "regular",
            [{"product_id": "notebook", "quantity": 2}],
            "express"
        )
        self.assertEqual(quote["delivery_cents"], 1200)
        self.assertEqual(quote["total_cents"], 2200)

    # Test 6: Student discount with express delivery
    def test_student_express_discount(self):
        quote = self.service.quote(
            "student",
            [{"product_id": "hoodie", "quantity": 2}],
            "express"
        )
        self.assertEqual(quote["subtotal_cents"], 8000)
        self.assertEqual(quote["discount_cents"], 800)
        self.assertEqual(quote["delivery_cents"], 1200)
        self.assertEqual(quote["total_cents"], 8400)

    # Test 7: Express fee is never waived
    def test_express_fee_not_waived(self):
        quote = self.service.quote(
            "regular",
            [{"product_id": "hoodie", "quantity": 3}],
            "express"
        )
        self.assertEqual(quote["delivery_cents"], 1200)
        self.assertEqual(quote["total_cents"], 13200)

    # Test 8: Standard delivery remains unchanged
    def test_standard_delivery_unchanged(self):
        quote = self.service.quote(
            "regular",
            [{"product_id": "hoodie", "quantity": 3}],
            "delivery"
        )
        self.assertEqual(quote["delivery_cents"], 0)
        self.assertEqual(quote["total_cents"], 12000)

    # Test 9: Invalid fulfillment is rejected
    def test_invalid_fulfillment(self):
        with self.assertRaises(ValueError):
            self.service.quote(
                "regular",
                [{"product_id": "notebook", "quantity": 1}],
                "overnight"
            )

    # Test 10: Express quote and placed order agree
    def test_express_quote_matches_order(self):
        items = [{"product_id": "notebook", "quantity": 2}]

        quote = self.service.quote("regular", items, "express")
        order = self.service.place_order("regular", items, "express")

        for key in (
            "fulfillment",
            "items",
            "subtotal_cents",
            "discount_cents",
            "delivery_cents",
            "total_cents"
        ):
            self.assertEqual(quote[key], order[key])

    # Test 11: Express order survives reload and cancellation
    def test_express_order_persistence_and_cancellation(self):
        items = [{"product_id": "notebook", "quantity": 2}]
        order = self.service.place_order("regular", items, "express")

        reloaded_service = OrderService(
            Path(self.directory.name) / "state.json"
        )
        saved_order = reloaded_service.get_order(order["order_id"])

        self.assertEqual(saved_order["fulfillment"], "express")
        self.assertEqual(saved_order["delivery_cents"], 1200)
        self.assertEqual(saved_order["total_cents"], 2200)
        self.assertEqual(saved_order["items"], order["items"])

        cancelled = reloaded_service.cancel_order(order["order_id"])

        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(cancelled["fulfillment"], "express")
        self.assertEqual(cancelled["delivery_cents"], 1200)
        self.assertEqual(cancelled["total_cents"], 2200)
        self.assertEqual(cancelled["items"], order["items"])


if __name__ == "__main__":
    unittest.main()
