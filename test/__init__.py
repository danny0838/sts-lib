import unittest
import os
import re
from sts import StsListMaker, StsConverter, Unicode, StsDict, Table, Trie

root_dir = os.path.dirname(__file__)


class TestClassUnicode(unittest.TestCase):
    def test_split(self):
        self.assertEqual(Unicode.split('沙⿰虫风简转繁'), ['沙', '⿰虫风', '简', '转', '繁'])
        self.assertEqual(Unicode.split('沙⿱艹⿰虫风简转繁'), ['沙', '⿱艹⿰虫风', '简', '转', '繁'])
        self.assertEqual(Unicode.split('「⿰⿱⿲⿳」不影響'), ['「', '⿰⿱⿲⿳', '」', '不', '影', '響'])
        self.assertEqual(Unicode.split('⿰⿱⿲⿳ 不影響'), ['⿰⿱⿲⿳', ' ', '不', '影', '響'])
        self.assertEqual(Unicode.split('⿸⿹⿺⿻\n不影響'), ['⿸⿹⿺⿻', '\n', '不', '影', '響'])
        self.assertEqual(Unicode.split('⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻長度不夠'), ['⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻長度不夠'])
        self.assertEqual(Unicode.split('刀〾劍 〾劍訢 劍〾訢 〾劍〾訢'), ['刀', '〾劍', ' ', '〾劍', '訢', ' ', '劍', '〾訢', ' ', '〾劍', '〾訢'])
        self.assertEqual(Unicode.split('刀劍󠄁 劍󠄃訢'), ['刀' ,'劍󠄁', ' ', '劍󠄃', '訢'])
        self.assertEqual(Unicode.split('刀劍󠄁󠄂 劍󠄁󠄂訢'), ['刀', '劍󠄁󠄂', ' ', '劍󠄁󠄂', '訢'])
        self.assertEqual(Unicode.split('⿱𠀀𠀀芀⿱〾艹劍󠄁無情'),  ['⿱𠀀𠀀', '芀', '⿱〾艹劍󠄁', '無', '情'])

        self.assertEqual(Unicode.split('A片 Å片 A̧片 Å̧片'), ['A', '片', ' ', 'Å', '片', ' ', 'A̧', '片', ' ', 'Å̧', '片'])
        self.assertEqual(Unicode.split('áéíóúý'), ['á', 'é', 'í', 'ó', 'ú', 'ý'])
        self.assertEqual(Unicode.split('áéíóúý'), ['á', 'é', 'í', 'ó', 'ú', 'ý'])
        self.assertNotEqual(Unicode.split('áéíóúý'), Unicode.split('áéíóúý'))
        self.assertEqual(Unicode.split('Lorem ipsum dolor sit amet.'), [
            'L', 'o', 'r', 'e', 'm', ' ',
            'i', 'p', 's', 'u', 'm', ' ',
            'd', 'o', 'l', 'o', 'r', ' ',
            's', 'i', 't', ' ',
            'a', 'm', 'e', 't', '.'])


class TestClassStsDict(unittest.TestCase):
    def prepare_dicts(self, *args, **kwargs):
        d1 = StsDict(*args, **kwargs)
        d2 = Table().add_dict(d1)
        d3 = Trie().add_dict(d1)
        return d1, d2, d3

    def test_iter(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']}):
            self.assertEqual(list(stsdict.iter()), [('干', ['幹', '乾']), ('干姜', ['乾薑']), ('姜', ['姜', '薑'])])

    def test_add(self):
        for stsdict in self.prepare_dicts():
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
            stsdict2 = StsDict({'干': ['干', '榦'], '姜': ['姜', '薑']})
            stsdict.add_dict(stsdict2)
            self.assertEqual(list(stsdict.iter()), [('干', ['幹', '乾', '干', '榦']), ('姜', ['姜', '薑'])])

    def test_match(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']}):
            self.assertEqual(stsdict.match('吃干姜了', 0), None)
            self.assertEqual(stsdict.match('吃干姜了', 1), ((['干', '姜'], ['乾薑']), 1, 3))
            self.assertEqual(stsdict.match('吃干姜了', 2), ((['姜'], ['姜', '薑']), 2, 3))
            self.assertEqual(stsdict.match('吃干姜了', 3), None)

    def test_apply(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']}):
            self.assertEqual(list(stsdict.apply('吃干姜了')), ['吃', (['干', '姜'], ['乾薑']), '了'])

    def test_apply_enum(self):
        for stsdict in self.prepare_dicts({'钟': ['鐘', '鍾'], '药': ['藥', '葯'], '用药': ['用藥']}):
            self.assertEqual(
                stsdict.apply_enum('看钟用药', include_short=False, include_self=False),
                ['看鐘用藥', '看鍾用藥'])
            self.assertEqual(
                stsdict.apply_enum('看钟用药', include_short=True, include_self=False),
                ['看鐘用藥', '看鐘用葯', '看鍾用藥', '看鍾用葯'])
            self.assertEqual(
                stsdict.apply_enum('看钟用药', include_short=False, include_self=True),
                ['看鐘用藥', '看鐘用药', '看鍾用藥', '看鍾用药', '看钟用藥', '看钟用药'])
            self.assertEqual(
                stsdict.apply_enum('看钟用药', include_short=True, include_self=True),
                ['看鐘用藥', '看鐘用药', '看鐘用葯', '看鍾用藥', '看鍾用药', '看鍾用葯', '看钟用藥', '看钟用药', '看钟用葯'])

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
            stsdict2 = Table({'注': ['注', '註']})
            stsdict = stsdict._join_prefix(stsdict2)
            self.assertEqual(list(stsdict.iter()), [('注冊表', ['登錄檔']), ('註冊表', ['登錄檔'])])

    def test_postfix(self):
        for stsdict in self.prepare_dicts({'因为': ['因爲']}):
            stsdict2 = Table({'爲': ['為']})
            stsdict = stsdict._join_postfix(stsdict2)
            self.assertEqual(list(stsdict.iter()), [('因为', ['因為']), ('爲', ['為'])])


class TestSts(unittest.TestCase):
    def convert_text(self, text, config, options={}, method='convert_text'):
        stsdict = StsListMaker().make(config, quiet=True)
        converter = StsConverter(stsdict, options)
        return getattr(converter, method)(text)

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


class TestFormat(TestSts):
    def test_generator(self):
        text = """干了 干涉
⿰虫风需要简转繁
⿱艹⿰虫风不需要简转繁
沙⿰虫风也简转繁"""
        self.assertEqual(
            list(self.convert_text(text, 's2t', method='convert')), 
            [(['干', '了'], ['幹了', '乾了']), ' ', (['干', '涉'], ['干涉']), '\n', '⿰虫风', '需', '要', (['简'], ['簡']), (['转'], ['轉']), '繁', '\n', '⿱艹⿰虫风', '不', '需', '要', (['简'], ['簡']), (['转'], ['轉']), '繁', '\n', '沙', '⿰虫风', '也', (['简'], ['簡']), (['转'], ['轉']), '繁'])

    def test_txtm(self):
        self.check_case('test_format', 'format_txtm', options={'format': 'txtm'})

    def test_html(self):
        self.check_case('test_format', 'format_html', options={'format': 'html'})

    def test_json(self):
        self.check_case('test_format', 'format_json', options={'format': 'json'})


@unittest.skip
class TestConfigs(unittest.TestCase):
    def test_configs(self):
        def clear_lists():
            pattern = re.compile(r'\.(?:[jt]?list)$', re.I)
            for fh in os.scandir(config_dir):
                if pattern.search(fh.path):
                    os.remove(fh)

        config_dir = StsListMaker.DEFAULT_CONFIG_DIR
        maker = StsListMaker()
        pattern = re.compile(r'\.json$', re.I)
        for file in os.listdir(config_dir):
            if pattern.search(file):
                clear_lists()
                maker.make(file, quiet=True)


if __name__ == '__main__':
    unittest.main()
