import json
import logging
import os
import unittest

import yaml

from sts.common import StsConverter, StsMaker

from . import slow_test

root_dir = os.path.dirname(__file__)


def setUpModule():
    # suppress logging
    logging.disable(logging.CRITICAL)


def tearDownModule():
    # unsuppress logging
    logging.disable(logging.NOTSET)


@slow_test()
class TestMake(unittest.TestCase):
    def _clear_generated_dicts(self, config_dir):
        dicts_dir = os.path.normpath(os.path.join(config_dir, '..', 'dictionary'))
        with os.scandir(dicts_dir) as it:
            for entry in it:
                if not entry.is_file:
                    continue
                if not os.path.splitext(entry)[1].lower() in ('.tlist', '.jlist'):
                    continue

                os.remove(entry)

    def _test_make_config_files(self, config_dir):
        with os.scandir(config_dir) as it:
            for entry in it:
                if not entry.is_file:
                    continue
                if not os.path.splitext(entry)[1].lower() == '.yaml':
                    continue

                with self.subTest(config=entry.path):
                    self._clear_generated_dicts(config_dir)
                    StsMaker().make(entry)

    def test_make(self):
        """Check if built-in configs can be made independently."""
        config_dir = StsMaker.config_dir
        self._test_make_config_files(config_dir)

    def test_make_external(self):
        """Check if external configs can be made independently."""
        with os.scandir(os.path.join(StsMaker.data_dir, 'external')) as it:
            for entry in it:
                config_dir = os.path.join(entry, 'config')
                if not os.path.isdir(config_dir):
                    continue

                self._test_make_config_files(config_dir)


class TestConfigs(unittest.TestCase):
    def _iter_testcase_files(self, ref_dir):
        with os.scandir(ref_dir) as it:
            for entry in it:
                if not entry.is_file:
                    continue
                if not os.path.splitext(entry)[1].lower() in ('.yaml', '.json'):
                    continue
                yield entry

    def _test_against_testcase_file(self, test_file, config_dir=None, converters=None):
        with open(test_file, encoding='utf-8') as fh:
            if os.path.splitext(test_file)[1].lower() == '.json':
                data = json.load(fh)
            else:
                data = yaml.safe_load(fh)

        for i, case in enumerate(data['cases']):
            self._test_against_case(i, case, config_dir, converters)

    def _test_against_case(self, i, case, config_dir, converters):
        input = case['input']
        for config, expected in case['expected'].items():
            if config_dir is not None:
                config = os.path.join(config_dir, f'{config}.yaml')
            with self.subTest(id=case.get('id', i), input=input, config=config):
                self._test_against_config(config, input, expected, converters)

    def _test_against_config(self, config, input, expected, converters):
        try:
            converter = converters[config]
        except KeyError:
            dict_ = StsMaker().make(config)
            converter = converters[config] = StsConverter(dict_)

        if isinstance(expected, str):
            output = converter.convert_text(input)
        else:
            output = [x if isinstance(x, str) else x.values for x in converter.convert(input)]

        self.assertEqual(expected, output)

    def test_configs(self):
        """Test configs with files at tests/test_data_configs/*.{yaml,json}"""
        converters = {}
        test_dir = os.path.join(root_dir, 'test_data_configs')
        for entry in self._iter_testcase_files(test_dir):
            with self.subTest(src=entry.name):
                self._test_against_testcase_file(entry, converters=converters)

    def test_configs_external(self):
        """Test external configs with files at sts/data/external/*/tests/*.{yaml,json}"""
        converters = {}
        with os.scandir(os.path.join(StsMaker.data_dir, 'external')) as it:
            for entry in it:
                config_dir = os.path.join(entry, 'config')
                if not os.path.isdir(config_dir):
                    continue

                test_dir = os.path.join(entry, 'tests')
                if not os.path.isdir(test_dir):
                    continue

                for entry in self._iter_testcase_files(test_dir):
                    with self.subTest(src=entry.path):
                        self._test_against_testcase_file(entry, config_dir=config_dir, converters=converters)


if __name__ == '__main__':
    unittest.main()
