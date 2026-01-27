import tempfile
import unittest

from app.constants import MATCH_DECISION_LIKED, ORDER_STATUS_OPEN
from app.db import Database


class DatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.db = Database(self.tmp.name)
        await self.db.init()

    async def asyncTearDown(self):
        self.tmp.close()

    async def test_user_and_order(self):
        user = await self.db.create_user(123, "+79990001122")
        await self.db.set_user_roles(user["id"], is_customer=True)
        await self.db.update_user_profile(user["id"], "Иван", "Иванов", "ООО")
        order = await self.db.create_order(
            user["id"],
            {
                "name": "Тест",
                "doc_types": ["ПД"],
                "construction_types": ["линейные объекты"],
                "sections_capital": [],
                "sections_linear": ["ПЗ (пояснительная записка)"],
                "description": "Описание",
                "deadline": "2025-01-01",
                "price": "1000",
                "expertise_required": True,
                "files_link": "https://example.com",
                "status": ORDER_STATUS_OPEN,
            },
        )
        self.assertEqual(order["customer_id"], user["id"])

    async def test_match_and_rating(self):
        cust = await self.db.create_user(1, "+70000000001")
        execu = await self.db.create_user(2, "+70000000002")
        await self.db.set_user_roles(cust["id"], is_customer=True)
        await self.db.set_user_roles(execu["id"], is_executor=True)
        order = await self.db.create_order(
            cust["id"],
            {
                "name": "Заказ",
                "doc_types": ["ПД"],
                "construction_types": ["линейные объекты"],
                "sections_capital": [],
                "sections_linear": ["ПЗ (пояснительная записка)"],
                "description": "",
                "deadline": "2025-01-01",
                "price": "1000",
                "expertise_required": False,
                "files_link": "https://example.com",
                "status": ORDER_STATUS_OPEN,
            },
        )
        await self.db.upsert_match(order["id"], execu["id"], customer_decision=MATCH_DECISION_LIKED)
        match = await self.db.get_match(order["id"], execu["id"])
        self.assertEqual(match["customer_decision"], MATCH_DECISION_LIKED)
        await self.db.add_rating(order["id"], cust["id"], execu["id"], 5, "Отлично")
        avg, cnt = await self.db.get_rating_summary(execu["id"])
        self.assertEqual(cnt, 1)
        self.assertEqual(avg, 5.0)


if __name__ == "__main__":
    unittest.main()
