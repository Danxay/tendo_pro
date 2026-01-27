import unittest
import html
from app.services import format_order, format_customer_profile, format_executor_card, format_executor_profile

class TestHtmlInjection(unittest.TestCase):
    def test_format_order_injection(self):
        order = {
            "id": 1,
            "name": "<b>Evil Order</b>",
            "doc_types": ["<script>alert(1)</script>"],
            "construction_types": [],
            "sections_capital": [],
            "sections_linear": [],
            "description": "<i>Italic</i>",
            "deadline": "2025-01-01",
            "price": "1000",
            "expertise_required": False,
            "files_link": "http://example.com",
            "status": "open",
        }

        output = format_order(order)
        print(f"Output: {output}")

        # Now we expect tags to be ESCAPED
        self.assertNotIn("<b>", output)
        self.assertIn("&lt;b&gt;", output)

        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)

        self.assertNotIn("<i>", output)
        self.assertIn("&lt;i&gt;", output)

if __name__ == "__main__":
    unittest.main()
