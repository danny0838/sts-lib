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
    def _test_against_testcase_dir(self, test_dir, config_dir=None, converters=None):
        if not os.path.isdir(test_dir):
            return

        with os.scandir(test_dir) as it:
            for entry in it:
                if not entry.is_file:
                    continue

                _, ext = os.path.splitext(entry.name)
                ext = ext.lower()
                if ext not in ('.yaml', '.json'):
                    continue

                test_file = entry.path
                with self.subTest(src=test_file):
                    with open(test_file, encoding='utf-8') as fh:
                        data = json.load(fh) if ext == '.json' else yaml.safe_load(fh)

                    cases = {case.get('id', i): case for i, case in enumerate(data.get('cases', ()))}

                    for id_, case in cases.items():
                        with self.subTest(id=id_):
                            self._test_against_case(id_, case, config_dir, converters)

    def _test_against_case(self, id, case, config_dir, converters):
        input = case['input']
        for field in ('expected', 'expected_raw'):
            for config, expected in case.get(field, {}).items():
                if config_dir is not None:
                    config = os.path.join(config_dir, f'{config}.yaml')
                with self.subTest(id=id, input=input, field=field, config=config):
                    self._test_against_config(field, input, config, expected, converters)

    def _test_against_config(self, field, input, config, expected, converters):
        try:
            converter = converters[config]
        except KeyError:
            dict_ = StsMaker().make(config)
            converter = converters[config] = StsConverter(dict_)

        if field == 'expected':
            output = converter.convert_text(input)
        elif field == 'expected_raw':
            output = [x if isinstance(x, str) else x.values for x in converter.convert(input)]

        self.assertEqual(expected, output)

    def test_configs(self):
        """Test configs with files at tests/test_data_configs/*.{yaml,json}"""
        converters = {}
        test_dir = os.path.join(root_dir, 'test_data_configs')
        self._test_against_testcase_dir(test_dir, converters=converters)

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

                self._test_against_testcase_dir(test_dir, config_dir=config_dir, converters=converters)


if __name__ == '__main__':
    unittest.main()
