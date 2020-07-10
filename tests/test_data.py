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

    def test_cases(self):
        stsdict = StsMaker().make('s2tw', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual('高級設置默認的幾率是50%', converter.convert_text('高级设置默认的几率是50%'))

        stsdict = StsMaker().make('s2twp', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual('高階設定預設的機率是50%', converter.convert_text('高级设置默认的几率是50%'))

        stsdict = StsMaker().make('tw2t', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual('進階設定預設的機率是50%', converter.convert_text('進階設定預設的機率是50%'))

        stsdict = StsMaker().make('tw2s', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual('进阶设定预设的机率是50%', converter.convert_text('進階設定預設的機率是50%'))

        stsdict = StsMaker().make('tw2sp', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual('高级设置默认的概率是50%', converter.convert_text('進階設定預設的機率是50%'))

        stsdict = StsMaker().make('s2hk', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual('幾率很大', converter.convert_text('几率很大'))

        stsdict = StsMaker().make('s2hkp', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual('機會率很大', converter.convert_text('几率很大'))

        stsdict = StsMaker().make('hk2t', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual('機率不低', converter.convert_text('機率不低'))

        stsdict = StsMaker().make('hk2s', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual('机率不低', converter.convert_text('機率不低'))
        self.assertEqual('机会率不低', converter.convert_text('機會率不低'))

        stsdict = StsMaker().make('hk2sp', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual('概率不低', converter.convert_text('機率不低'))
        self.assertEqual('概率不低', converter.convert_text('機會率不低'))

    def test_t2jp(self):
        stsdict = StsMaker().make('t2jp', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual('彎腰 搔擾 攪乱 幷用', converter.convert_text('彎腰 搔擾 攪亂 幷用'))

        stsdict = StsMaker().make('t2jpx', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual('弯腰 掻擾 撹乱 并用', converter.convert_text('彎腰 搔擾 攪亂 幷用'))


if __name__ == '__main__':
    unittest.main()
