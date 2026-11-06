
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


if __name__ == "__main__":
    unittest.main()
