import unittest

from app.constants import CONSTRUCTION_TYPES, SECTIONS_CAPITAL, SECTIONS_LINEAR
from app.services import has_match


class MatchingTests(unittest.TestCase):
    def test_match_capital(self):
        order = {
            "construction_types": [CONSTRUCTION_TYPES[0]],
            "sections_capital": [SECTIONS_CAPITAL[0]],
            "sections_linear": [],
        }
        executor = {
            "construction_types": [CONSTRUCTION_TYPES[0]],
            "sections_capital": [SECTIONS_CAPITAL[0]],
            "sections_linear": [],
        }
        self.assertTrue(has_match(order, executor))

    def test_no_match(self):
        order = {
            "construction_types": [CONSTRUCTION_TYPES[1]],
            "sections_capital": [],
            "sections_linear": [SECTIONS_LINEAR[0]],
        }
        executor = {
            "construction_types": [CONSTRUCTION_TYPES[0]],
            "sections_capital": [SECTIONS_CAPITAL[0]],
            "sections_linear": [],
        }
        self.assertFalse(has_match(order, executor))


if __name__ == "__main__":
    unittest.main()
