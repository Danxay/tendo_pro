import unittest

from app.validation import is_valid_name, is_valid_url, normalize_phone, parse_date


class ValidationTests(unittest.TestCase):
    def test_name_validation(self):
        self.assertTrue(is_valid_name("Иван"))
        self.assertTrue(is_valid_name("Anna Maria"))
        self.assertFalse(is_valid_name("123"))

    def test_url_validation(self):
        self.assertTrue(is_valid_url("https://example.com/file"))
        self.assertFalse(is_valid_url("not-a-url"))

    def test_date_parse(self):
        self.assertEqual(parse_date("31.12.2024").isoformat(), "2024-12-31")
        self.assertEqual(parse_date("2025-01-10").isoformat(), "2025-01-10")
        self.assertIsNone(parse_date("2024/12/31"))

    def test_phone_normalize(self):
        self.assertEqual(normalize_phone("+7 (999) 123-45-67"), "+79991234567")
        self.assertEqual(normalize_phone("8 999 123 45 67"), "+79991234567")


if __name__ == "__main__":
    unittest.main()
