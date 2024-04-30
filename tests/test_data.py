import os
import re
import unittest

import yaml

from sts import StsConverter, StsMaker

from . import slow_test

root_dir = os.path.dirname(__file__)


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

    def _test_config(self, config):
        test_file = os.path.join(root_dir, 'test_data_config', f'{config}.yaml')
        with open(test_file, encoding='utf-8') as fh:
            data = yaml.safe_load(fh)

        dict_ = StsMaker().make(config, quiet=True)
        converter = StsConverter(dict_)
        for test in data['tests']:
            if 'group' in test:
                group = test['group']
                subtests = test['tests']
                with self.subTest(group=group):
                    for subtest in subtests:
                        self._test_config_test(converter, subtest)
            else:
                with self.subTest(msg=test['texts'][1]):
                    self._test_config_test(converter, test)

    def _test_config_test(self, converter, test):
        input, expected = test['texts']
        if isinstance(expected, str):
            self.assertEqual(expected, converter.convert_text(input))
        else:
            output = [list(x) if isinstance(x, tuple) else x for x in converter.convert(input)]
            self.assertEqual(expected, output)

    def test_config_s2t(self):
        self._test_config('s2t')

    def test_config_t2s(self):
        self._test_config('t2s')

    def test_config_tw2t(self):
        self._test_config('hk2t')

    def test_config_s2tw(self):
        self._test_config('s2tw')

    def test_config_tw2s(self):
        self._test_config('tw2s')

    def test_config_s2twp(self):
        self._test_config('s2twp')

    def test_config_tw2sp(self):
        self._test_config('tw2sp')

    def test_config_t2hk(self):
        self._test_config('t2hk')

    def test_config_hk2t(self):
        self._test_config('hk2t')

    def test_config_s2hk(self):
        self._test_config('s2hk')

    def test_config_hk2s(self):
        self._test_config('hk2s')

    def test_config_t2jp(self):
        self._test_config('t2jp')

    def test_config_jp2t(self):
        self._test_config('jp2t')


if __name__ == '__main__':
    unittest.main()
