import os
import re
import unittest

from sts import StsMaker

from . import slow_test


class TestConfigs(unittest.TestCase):
    @slow_test()
    def test_make(self):
        """Check if built-in configs can be made independently."""
        def clear_generated_dicts():
            with os.scandir(dict_dir) as it:
                for file in it:
                    if dict_pattern.search(file.path):
                        os.remove(file)

        config_dir = StsMaker.config_dir
        dict_dir = StsMaker.dictionary_dir
        config_pattern = re.compile(r'\.json$', re.I)
        dict_pattern = re.compile(r'\.(?:[jt]?list)$', re.I)
        for file in os.listdir(config_dir):
            if not config_pattern.search(file):
                continue

            with self.subTest(config=file):
                clear_generated_dicts()
                StsMaker().make(file, quiet=True)


if __name__ == '__main__':
    unittest.main()
