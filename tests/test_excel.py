import unittest
import zipfile
from io import BytesIO

from app.excel import build_xlsx


class ExcelTests(unittest.TestCase):
    def test_build_xlsx(self):
        data = build_xlsx([["A", "B"], ["1", "2"]], sheet_name="Test")
        self.assertTrue(data)
        with zipfile.ZipFile(BytesIO(data)) as zf:
            names = set(zf.namelist())
        self.assertIn("[Content_Types].xml", names)
        self.assertIn("xl/workbook.xml", names)
        self.assertIn("xl/worksheets/sheet1.xml", names)


if __name__ == "__main__":
    unittest.main()
