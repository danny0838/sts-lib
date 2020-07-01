import unittest
import os
from pathlib import Path
from sts import StsListMaker, StsConverter, StsDict, Table, Trie

root_dir = os.path.dirname(__file__)
StsListMaker().make('_default', quiet=True)


class TestSts(unittest.TestCase):
    def convert_text(self, text, config, options={}):
        stsdict = StsListMaker().make(config, quiet=True)
        converter = StsConverter(stsdict, options)
        return converter.convert_text(text)

    def check_case(self, subdir, name, config=None, options={}):
        dir = os.path.join(root_dir, subdir)

        with open(os.path.join(dir, name + '.in'), 'r', encoding='UTF-8') as f:
            input = f.read()
            f.close()

        with open(os.path.join(dir, name + '.ans'), 'r', encoding='UTF-8') as f:
            answer = f.read()
            f.close()

        result = self.convert_text(input, config or os.path.join(dir, name + '.json'), options)
        self.assertEqual(result, answer)


class TestClassStsDict(TestSts):
    def prepare_dicts(self, dict_data):
        d1 = StsDict(dict_data)
        d2 = Table().add_dict(d1)
        d3 = Trie().add_dict(d1)
        return d1, d2, d3

    def test_iter(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']}):
            self.assertEqual(list(stsdict.iter()), [('干', ['幹', '乾']), ('干姜', ['乾薑']), ('姜', ['姜', '薑'])])

    def test_add(self):
        for stsdict in self.prepare_dicts({}):
            stsdict.add('干', ['幹', '乾'])
            self.assertEqual(list(stsdict.iter()), [('干', ['幹', '乾'])])
            stsdict.add('干', '干')
            self.assertEqual(list(stsdict.iter()), [('干', ['幹', '乾', '干'])])
            stsdict.add('干', ['榦'])
            self.assertEqual(list(stsdict.iter()), [('干', ['幹', '乾', '干', '榦'])])
            stsdict.add('姜', ['姜', '薑'])
            self.assertEqual(list(stsdict.iter()), [('干', ['幹', '乾', '干', '榦']), ('姜', ['姜', '薑'])])

    def test_add2(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾']}):
            stsdict.add('干', ['幹'])
            self.assertEqual(list(stsdict.iter()), [('干', ['幹', '乾'])])
            stsdict.add('干', ['乾'], skip_check=True)
            self.assertEqual(list(stsdict.iter()), [('干', ['幹', '乾', '乾'])])

    def test_add_dict(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾']}):
            stsdict2 = self.prepare_dicts({'干': ['干', '榦'], '姜': ['姜', '薑']})[0]
            stsdict.add_dict(stsdict2)
            self.assertEqual(list(stsdict.iter()), [('干', ['幹', '乾', '干', '榦']), ('姜', ['姜', '薑'])])

    def test_match(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']}):
            self.assertEqual(stsdict.match('吃干姜了', 0), None)
            self.assertEqual(stsdict.match('吃干姜了', 1), (('干姜', ['乾薑']), 1, 3))
            self.assertEqual(stsdict.match('吃干姜了', 2), (('姜', ['姜', '薑']), 2, 3))
            self.assertEqual(stsdict.match('吃干姜了', 3), None)

    def test_apply(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']}):
            self.assertEqual(list(stsdict.apply('吃干姜了')), ['吃', ('干姜', ['乾薑']), '了'])

    def test_apply_enum(self):
        for stsdict in self.prepare_dicts({'钟': ['鐘', '鍾'], '药': ['藥', '葯'], '用药': ['用藥']}):
            self.assertEqual(
                stsdict.apply_enum('看钟用药', include_short=False, include_self=False),
                ['看鐘用藥', '看鍾用藥'])
            self.assertEqual(
                stsdict.apply_enum('看钟用药', include_short=True, include_self=False),
                ['看鐘用藥', '看鍾用藥', '看鐘用葯', '看鍾用葯'])
            self.assertEqual(
                stsdict.apply_enum('看钟用药', include_short=False, include_self=True),
                ['看鐘用藥', '看鐘用药', '看鍾用藥', '看鍾用药', '看钟用藥', '看钟用药'])
            self.assertEqual(
                stsdict.apply_enum('看钟用药', include_short=True, include_self=True),
                ['看鐘用藥', '看鐘用药', '看鍾用藥', '看鍾用药', '看钟用藥', '看钟用药', '看鐘用葯', '看鍾用葯', '看钟用葯'])

    def test_apply_enum2(self):
        for stsdict in self.prepare_dicts({'采信': ['採信'], '信息': ['訊息']}):
            self.assertEqual(
                stsdict.apply_enum('采信息', include_short=False, include_self=False),
                ['採信息'])
            self.assertEqual(
                stsdict.apply_enum('采信息', include_short=True, include_self=False),
                ['採信息', '采訊息'])
            self.assertEqual(
                stsdict.apply_enum('采信息', include_short=False, include_self=True),
                ['採信息', '采信息'])
            self.assertEqual(
                stsdict.apply_enum('采信息', include_short=True, include_self=True),
                ['採信息', '采信息', '采訊息'])

    def test_prefix(self):
        for stsdict in self.prepare_dicts({'註冊表': ['登錄檔']}):
            stsdict2 = self.prepare_dicts({'注': ['注', '註']})[0]
            stsdict = stsdict._join_prefix(stsdict2)
            self.assertEqual(list(stsdict.iter()), [('注冊表', ['登錄檔']), ('註冊表', ['登錄檔'])])

    def test_postfix(self):
        for stsdict in self.prepare_dicts({'因为': ['因爲']}):
            stsdict2 = self.prepare_dicts({'爲': ['為']})[0]
            stsdict = stsdict._join_postfix(stsdict2)
            self.assertEqual(list(stsdict.iter()), [('因为', ['因為']), ('爲', ['為'])])


class TestDict(TestSts):
    def test_merge1(self):
        self.check_case('test_dict', 'merge1')

    def test_merge2(self):
        self.check_case('test_dict', 'merge2')

    def test_join1(self):
        self.check_case('test_dict', 'join1')

    def test_join2(self):
        self.check_case('test_dict', 'join2')

    def test_join3(self):
        self.check_case('test_dict', 'join3')

    def test_join4(self):
        self.check_case('test_dict', 'join4')


class TestIds(TestSts):
    def test_ids1(self):
        self.check_case('test_ids', 'ids1')

    def test_ids2(self):
        self.check_case('test_ids', 'ids2')

    def test_ids_broken1(self):
        self.check_case('test_ids', 'ids_broken1', 'tw2s')

    def test_vi1(self):
        self.check_case('test_ids', 'vi1')

    def test_vs1(self):
        self.check_case('test_ids', 'vs1')

    def test_cdm1(self):
        self.check_case('test_ids', 'cdm1')


class TestExclude(TestSts):
    def test_exclude1(self):
        self.check_case('test_exclude', 'exclude1', 's2t', {
            'exclude': r'-{(?P<return>.*?)}-',
            })

    def test_exclude2(self):
        self.check_case('test_exclude', 'exclude2', 's2t', {
            'exclude': r'<!-->(?P<return>.*?)<-->',
            })

    def test_exclude3(self):
        self.check_case('test_exclude', 'exclude3', 's2twp', {
            'exclude': r'「.*?」',
            })


if __name__ == '__main__':
    unittest.main()
