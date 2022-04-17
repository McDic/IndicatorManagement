import unittest

from src.indicator_management import generate_sync
from src.indicator_management.indicators import RawSeriesIndicator
from src.indicator_management.settings import (
    get_default_safe_none,
    set_default_safe_none,
)


class SettingsTest(unittest.TestCase):
    def test_safe_none_true(self):
        set_default_safe_none(True)
        self.assertEqual(get_default_safe_none(), True)
        raw1 = RawSeriesIndicator(raw_values=(None,))
        raw2 = RawSeriesIndicator(raw_values=(None,))
        add = raw1 + raw2
        for obj in generate_sync(add=add):
            self.assertEqual(obj["add"], None)

    def test_safe_none_false(self):
        set_default_safe_none(False)
        self.assertEqual(get_default_safe_none(), False)
        raw1 = RawSeriesIndicator(raw_values=(None,))
        raw2 = RawSeriesIndicator(raw_values=(None,))
        add = raw1 + raw2
        with self.assertRaises(TypeError):
            for obj in generate_sync(add=add):
                self.assertEqual(obj["add"], None)


if __name__ == "__main__":
    unittest.main()
