import io
import json
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from sts import (
    StreamList,
    StsConverter,
    StsDict,
    StsMaker,
    Table,
    Trie,
    Unicode,
)

from . import slow_test

root_dir = os.path.dirname(__file__)


def setUpModule():
    """Set up a temp directory for testing
    """
    global _tmpdir, tmpdir
    _tmpdir = tempfile.TemporaryDirectory(prefix='init-')
    tmpdir = _tmpdir.name


def tearDownModule():
    """Cleanup the temp directory
    """
    _tmpdir.cleanup()


class TestClassStreamList(unittest.TestCase):
    def test_iterable(self):
        obj = []
        stream = StreamList(iter(obj))
        self.assertFalse(stream)
        self.assertEqual(obj, list(stream))
        self.assertEqual([], list(stream))
        self.assertFalse(stream)

        obj = []
        stream = StreamList(iter(obj))
        self.assertEqual(obj, list(stream))
        self.assertEqual([], list(stream))
        self.assertFalse(stream)

        obj = [1, 2, 3]
        stream = StreamList(iter(obj))
        self.assertTrue(stream)
        self.assertEqual(obj, list(stream))
        self.assertEqual([], list(stream))
        self.assertTrue(stream)

        obj = [1, 2, 3]
        stream = StreamList(iter(obj))
        self.assertEqual(obj, list(stream))
        self.assertEqual([], list(stream))
        self.assertTrue(stream)

        obj = [None]
        stream = StreamList(iter(obj))
        self.assertTrue(stream)
        self.assertEqual(obj, list(stream))
        self.assertEqual([], list(stream))
        self.assertTrue(stream)

        obj = [None]
        stream = StreamList(iter(obj))
        self.assertEqual(obj, list(stream))
        self.assertEqual([], list(stream))
        self.assertTrue(stream)

    def test_list(self):
        obj = []
        stream = StreamList(obj)
        self.assertFalse(stream)
        self.assertEqual(obj, list(stream))
        self.assertEqual([], list(stream))
        self.assertFalse(stream)

        obj = []
        stream = StreamList(obj)
        self.assertEqual(obj, list(stream))
        self.assertEqual([], list(stream))
        self.assertFalse(stream)

        obj = [1, 2, 3]
        stream = StreamList(obj)
        self.assertTrue(stream)
        self.assertEqual(obj, list(stream))
        self.assertEqual([], list(stream))
        self.assertTrue(stream)

        obj = [1, 2, 3]
        stream = StreamList(obj)
        self.assertEqual(obj, list(stream))
        self.assertEqual([], list(stream))
        self.assertTrue(stream)

        obj = [None]
        stream = StreamList(obj)
        self.assertTrue(stream)
        self.assertEqual(obj, list(stream))
        self.assertEqual([], list(stream))
        self.assertTrue(stream)

        obj = [None]
        stream = StreamList(obj)
        self.assertEqual(obj, list(stream))
        self.assertEqual([], list(stream))
        self.assertTrue(stream)


class TestClassUnicode(unittest.TestCase):
    def test_split(self):
        self.assertEqual(['沙', '⿰虫风', '简', '转', '繁'], Unicode.split('沙⿰虫风简转繁'))
        self.assertEqual(['沙', '⿱艹⿰虫风', '简', '转', '繁'], Unicode.split('沙⿱艹⿰虫风简转繁'))
        self.assertEqual(['「', '⿰⿱⿲⿳', '」', '不', '影', '響'], Unicode.split('「⿰⿱⿲⿳」不影響'))
        self.assertEqual(['⿰⿱⿲⿳', ' ', '不', '影', '響'], Unicode.split('⿰⿱⿲⿳ 不影響'))
        self.assertEqual(['⿸⿹⿺⿻', '\n', '不', '影', '響'], Unicode.split('⿸⿹⿺⿻\n不影響'))
        self.assertEqual(['⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻長度不夠'], Unicode.split('⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻長度不夠'))
        self.assertEqual(['刀', '〾劍', ' ', '〾劍', '訢', ' ', '劍', '〾訢', ' ', '〾劍', '〾訢'], Unicode.split('刀〾劍 〾劍訢 劍〾訢 〾劍〾訢'))
        self.assertEqual(['刀', '劍󠄁', ' ', '劍󠄃', '訢'], Unicode.split('刀劍󠄁 劍󠄃訢'))
        self.assertEqual(['刀', '劍󠄁󠄂', ' ', '劍󠄁󠄂', '訢'], Unicode.split('刀劍󠄁󠄂 劍󠄁󠄂訢'))
        self.assertEqual(['⿱𠀀𠀀', '芀', '⿱〾艹劍󠄁', '無', '情'], Unicode.split('⿱𠀀𠀀芀⿱〾艹劍󠄁無情'))

        self.assertEqual(['A', '片', ' ', 'Å', '片', ' ', 'A̧', '片', ' ', 'Å̧', '片'], Unicode.split('A片 Å片 A̧片 Å̧片'))
        self.assertEqual(['á', 'é', 'í', 'ó', 'ú', 'ý'], Unicode.split('áéíóúý'))
        self.assertEqual(['á', 'é', 'í', 'ó', 'ú', 'ý'], Unicode.split('áéíóúý'))
        self.assertNotEqual(Unicode.split('áéíóúý'), Unicode.split('áéíóúý'))
        self.assertEqual(
            [
                'L', 'o', 'r', 'e', 'm', ' ',
                'i', 'p', 's', 'u', 'm', ' ',
                'd', 'o', 'l', 'o', 'r', ' ',
                's', 'i', 't', ' ',
                'a', 'm', 'e', 't', '.',
            ],
            Unicode.split('Lorem ipsum dolor sit amet.'),
        )


class TestClassStsDict(unittest.TestCase):
    def setUp(self):
        """Set up a sub temp directory for testing."""
        self.root = tempfile.mkdtemp(dir=tmpdir)

    def test_init(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
                self.assertEqual({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, stsdict)

                stsdict = class_(StsDict({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}))
                self.assertEqual(StsDict({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}), stsdict)

                stsdict = class_([('干', ['幹', '乾', '干']), ('姜', ['姜', '薑']), ('干姜', ['乾薑'])])
                self.assertEqual({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, stsdict)

                stsdict = class_(干=['幹', '乾', '干'], 姜=['姜', '薑'], 干姜=['乾薑'])
                self.assertEqual({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, stsdict)

    def test_repr(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
                self.assertEqual(stsdict, eval(repr(stsdict)))

    def test_getitem(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['幹', '乾', '干'], '豆干': ['豆乾']})
                self.assertEqual(['幹', '乾', '干'], stsdict['干'])
                self.assertEqual(['豆乾'], stsdict['豆干'])
                with self.assertRaises(KeyError):
                    stsdict['豆']
                with self.assertRaises(KeyError):
                    stsdict['豆乾']

    def test_contains(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['幹', '乾', '干'], '豆干': ['豆乾']})
                self.assertTrue('干' in stsdict)
                self.assertTrue('豆干' in stsdict)
                self.assertFalse('豆' in stsdict)
                self.assertFalse('豆乾' in stsdict)

    def test_len(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_()
                self.assertEqual(0, len(stsdict))

                stsdict = class_({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
                self.assertEqual(3, len(stsdict))

    def test_iter(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['幹', '乾', '干'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
                self.assertEqual({'干', '姜', '干姜'}, set(stsdict))

    def test_eq(self):
        dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_(dict_)
                self.assertTrue(stsdict == dict_)
                self.assertTrue(dict_ == stsdict)
                self.assertFalse(stsdict != dict_)
                self.assertFalse(dict_ != stsdict)

        dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
        dict2 = {'干姜': ['乾薑'], '干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_(dict_)
                self.assertTrue(stsdict == dict2)
                self.assertTrue(dict2 == stsdict)
                self.assertFalse(stsdict != dict2)
                self.assertFalse(dict2 != stsdict)

        dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
        dict2 = {'干姜': ['乾薑'], '干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_(dict_)
                stsdict2 = class_(dict2)
                self.assertTrue(stsdict == stsdict2)
                self.assertTrue(stsdict2 == stsdict)
                self.assertFalse(stsdict != stsdict2)
                self.assertFalse(stsdict2 != stsdict)

        dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
        dict2 = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_(dict_)
                self.assertFalse(stsdict == dict2)
                self.assertFalse(dict2 == stsdict)
                self.assertTrue(stsdict != dict2)
                self.assertTrue(dict2 != stsdict)

        dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
        dict2 = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_(dict_)
                self.assertFalse(stsdict == dict2)
                self.assertFalse(dict2 == stsdict)
                self.assertTrue(stsdict != dict2)
                self.assertTrue(dict2 != stsdict)

        dict_ = {'干': ['幹', '乾', '干', '𠏉'], '姜': ['姜', '薑']}
        dict2 = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_(dict_)
                self.assertFalse(stsdict == dict2)
                self.assertFalse(dict2 == stsdict)
                self.assertTrue(stsdict != dict2)
                self.assertTrue(dict2 != stsdict)

    def test_keys(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['幹', '乾', '干'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
                self.assertEqual({'干', '姜', '干姜'}, set(stsdict.keys()))

    def test_values(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['幹', '乾', '干'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
                self.assertEqual({('幹', '乾', '干'), ('姜', '薑'), ('乾薑',)}, {tuple(x) for x in stsdict.values()})

    def test_items(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
                self.assertEqual({'干': ['幹', '乾'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, dict(stsdict.items()))

    def test_add(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_()

                stsdict.add('干', ['幹', '乾'])
                self.assertEqual({'干': ['幹', '乾']}, stsdict)

                stsdict.add('干', '干')
                self.assertEqual({'干': ['幹', '乾', '干']}, stsdict)

                stsdict.add('干', ['榦'])
                self.assertEqual({'干': ['幹', '乾', '干', '榦']}, stsdict)

                stsdict.add('姜', ['姜', '薑'])
                self.assertEqual({'干': ['幹', '乾', '干', '榦'], '姜': ['姜', '薑']}, stsdict)

    def test_add2(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['幹', '乾']})

                stsdict.add('干', ['幹'])
                self.assertEqual({'干': ['幹', '乾']}, stsdict)

                stsdict.add('干', ['乾'], skip_check=True)
                self.assertEqual({'干': ['幹', '乾', '乾']}, stsdict)

    def test_update(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['幹', '乾']})

                dict_ = StsDict({'干': ['干'], '姜': ['姜', '薑']})
                stsdict.update(dict_)
                self.assertEqual({'干': ['幹', '乾', '干'], '姜': ['姜', '薑']}, stsdict)

                dict_ = {'干': ['干', '榦'], '干姜': ['乾薑']}
                stsdict.update(dict_)
                self.assertEqual({'干': ['幹', '乾', '干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, stsdict)

    def test_load(self):
        tempfile = os.path.join(self.root, 'test.tmp')
        tempfile2 = os.path.join(self.root, 'test2.tmp')

        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""干\t幹 乾""")
        with open(tempfile2, 'w', encoding='UTF-8') as fh:
            fh.write("""干\t干 榦\n姜\t姜 薑""")

        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_()
                stsdict.load(tempfile, tempfile2)
                self.assertEqual({'干': ['幹', '乾', '干', '榦'], '姜': ['姜', '薑']}, stsdict)

        # check for cases of 0 or 2+ tabs
        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""干\t幹 乾\t# 一些註解\n姜\n干\t干\n\n干\t榦""")
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_()
                stsdict.load(tempfile)
                self.assertEqual({'干': ['幹', '乾', '干', '榦']}, stsdict)

    def test_dump(self):
        tempfile = os.path.join(self.root, 'test.tmp')

        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['干', '榦'], '姜': ['姜', '薑']})

                stsdict.dump(tempfile)
                with open(tempfile, 'r', encoding='UTF-8') as fh:
                    text = fh.read()
                self.assertEqual('干\t干 榦\n姜\t姜 薑\n', text)

                stsdict.dump(tempfile, sort=True)
                with open(tempfile, 'r', encoding='UTF-8') as fh:
                    text = fh.read()
                self.assertEqual('姜\t姜 薑\n干\t干 榦\n', text)

    def test_dump_stdout(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['干', '榦'], '姜': ['姜', '薑']})
                with redirect_stdout(io.StringIO()) as fh:
                    stsdict.dump()
                self.assertEqual('干\t干 榦\n姜\t姜 薑\n', fh.getvalue())

    def test_loadjson(self):
        tempfile = os.path.join(self.root, 'test.tmp')

        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write('{"干": ["干", "榦"], "姜": ["姜", "薑"], "干姜": ["乾薑"]}')
        stsdict = StsDict().loadjson(tempfile)
        self.assertEqual({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, stsdict)

        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write('{"干": ["干", "榦"], "姜": ["姜", "薑"], "干姜": ["乾薑"]}')
        stsdict = Table().loadjson(tempfile)
        self.assertEqual({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, stsdict)

        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write('{"干": {"": ["干", "榦"], "姜": {"": ["乾薑"]}}, "姜": {"": ["姜", "薑"]}}')
        stsdict = Trie().loadjson(tempfile)
        self.assertEqual({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, stsdict)

    def test_dumpjson(self):
        tempfile = os.path.join(self.root, 'test.tmp')

        stsdict = StsDict({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        stsdict.dumpjson(tempfile)
        with open(tempfile, 'r', encoding='UTF-8') as fh:
            self.assertEqual({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, json.load(fh))

        stsdict = Table({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        stsdict.dumpjson(tempfile)
        with open(tempfile, 'r', encoding='UTF-8') as fh:
            self.assertEqual({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, json.load(fh))

        stsdict = Trie({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        stsdict.dumpjson(tempfile)
        with open(tempfile, 'r', encoding='UTF-8') as fh:
            self.assertEqual({'干': {'': ['干', '榦'], '姜': {'': ['乾薑']}}, '姜': {'': ['姜', '薑']}}, json.load(fh))

    def test_dumpjson_stdout(self):
        stsdict = StsDict({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        with redirect_stdout(io.StringIO()) as fh:
            stsdict.dumpjson()
        self.assertEqual({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, json.loads(fh.getvalue()))

    def test_match(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
                self.assertIsNone(stsdict.match('吃干姜了', 0))
                self.assertEqual(((['干', '姜'], ['乾薑']), 1, 3), stsdict.match('吃干姜了', 1))
                self.assertEqual(((['姜'], ['姜', '薑']), 2, 3), stsdict.match('吃干姜了', 2))
                self.assertIsNone(stsdict.match('吃干姜了', 3))

    def test_apply(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
                self.assertEqual(['吃', (['干', '姜'], ['乾薑']), '了'], list(stsdict.apply('吃干姜了')))

    def test_apply_enum(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'钟': ['鐘', '鍾'], '药': ['藥', '葯'], '用药': ['用藥']})
                self.assertEqual(
                    ['看鐘用藥', '看鍾用藥'],
                    stsdict.apply_enum('看钟用药', include_short=False, include_self=False),
                )
                self.assertEqual(
                    ['看鐘用藥', '看鐘用葯', '看鍾用藥', '看鍾用葯'],
                    stsdict.apply_enum('看钟用药', include_short=True, include_self=False),
                )
                self.assertEqual(
                    ['看鐘用藥', '看鐘用药', '看鍾用藥', '看鍾用药', '看钟用藥', '看钟用药'],
                    stsdict.apply_enum('看钟用药', include_short=False, include_self=True),
                )
                self.assertEqual(
                    ['看鐘用藥', '看鐘用药', '看鐘用葯', '看鍾用藥', '看鍾用药', '看鍾用葯', '看钟用藥', '看钟用药', '看钟用葯'],
                    stsdict.apply_enum('看钟用药', include_short=True, include_self=True),
                )

    def test_apply_enum2(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'采信': ['採信'], '信息': ['訊息']})
                self.assertEqual(
                    ['採信息'],
                    stsdict.apply_enum('采信息', include_short=False, include_self=False),
                )
                self.assertEqual(
                    ['採信息', '采訊息'],
                    stsdict.apply_enum('采信息', include_short=True, include_self=False),
                )
                self.assertEqual(
                    ['採信息', '采信息'],
                    stsdict.apply_enum('采信息', include_short=False, include_self=True),
                )
                self.assertEqual(
                    ['採信息', '采信息', '采訊息'],
                    stsdict.apply_enum('采信息', include_short=True, include_self=True),
                )

    def test_prefix(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'註冊表': ['登錄檔']})
                stsdict2 = Table({'注': ['註', '注']})
                stsdict = stsdict._join_prefix(stsdict2)
                self.assertEqual({'注冊表': ['登錄檔'], '註冊表': ['登錄檔']}, stsdict)

        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'註冊表': ['登錄檔']})
                stsdict2 = Table({'注': ['注', '註']})
                stsdict = stsdict._join_prefix(stsdict2)
                self.assertEqual({'注冊表': ['注冊表', '登錄檔'], '註冊表': ['登錄檔']}, dict(stsdict))

        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'注冊表': [], '註冊表': ['登錄檔']})
                stsdict2 = Table({'注': ['注', '註']})
                stsdict = stsdict._join_prefix(stsdict2)
                self.assertEqual({'注冊表': ['注冊表', '登錄檔'], '註冊表': ['登錄檔']}, stsdict)

        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'註冊表': ['登錄檔']})
                stsdict2 = Table({'注': ['注', '註'], '册': ['冊'], '注册': ['註冊']})
                stsdict = stsdict._join_prefix(stsdict2)
                self.assertEqual({'注册表': ['登錄檔'], '註冊表': ['登錄檔'], '註册表': ['登錄檔'], '注冊表': ['注冊表', '登錄檔']}, stsdict)

    def test_postfix(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'因为': ['因爲']})
                stsdict2 = Table({'爲': ['為']})
                stsdict = stsdict._join_postfix(stsdict2)
                self.assertEqual({'因为': ['因為'], '爲': ['為']}, stsdict)

    def test_join(self):
        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'则': ['則'], '达': ['達'], '规': ['規']})
                stsdict2 = Table({'正則表達式': ['正規表示式'], '表達式': ['表示式']})
                stsdict = stsdict.join(stsdict2)
                self.assertEqual({
                    '则': ['則'], '达': ['達'], '规': ['規'],
                    '正則表達式': ['正規表示式'], '表達式': ['表示式'],
                    '正则表达式': ['正規表示式'], '正则表達式': ['正規表示式'], '正則表达式': ['正規表示式'],
                    '表达式': ['表示式'],
                }, stsdict)

        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({
                    '万用字元': ['萬用字元'], '数据': ['數據'],
                    '万': ['萬', '万'], '数': ['數'], '据': ['據', '据'], '问': ['問'], '题': ['題'],
                })
                stsdict2 = Table({'元數據': ['後設資料'], '數據': ['資料']})
                stsdict = stsdict.join(stsdict2)
                self.assertEqual({
                    '万用字元': ['萬用字元'], '数据': ['資料'],
                    '万': ['萬', '万'], '数': ['數'], '据': ['據', '据'], '问': ['問'], '题': ['題'],
                    '元數據': ['後設資料'], '數據': ['資料'],
                    '元数据': ['後設資料'], '元数據': ['後設資料'], '元數据': ['後設資料'],
                    '数據': ['資料'], '數据': ['資料'],
                }, stsdict)

        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'妳': ['你', '奶']})
                stsdict2 = Table({'奶媽': ['奶娘']})
                stsdict = stsdict.join(stsdict2)
                self.assertEqual({
                    '妳': ['你', '奶'],
                    '奶媽': ['奶娘'],
                    '妳媽': ['妳媽', '奶娘'],
                }, stsdict)

        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'汇': ['匯', '彙'], '编': ['編'], '汇编': ['彙編']})
                stsdict2 = Table({'彙編': ['組譯']})
                stsdict = stsdict.join(stsdict2)
                self.assertEqual({
                    '彙編': ['組譯'], '彙编': ['組譯'], '汇': ['匯', '彙'],
                    '汇編': ['汇編', '組譯'], '汇编': ['組譯'], '编': ['編'],
                }, stsdict)

        for class_ in (StsDict, Table, Trie):
            with self.subTest(type=class_):
                stsdict = class_({'干': ['幹', '乾', '干'], '白干': ['白幹', '白干']})
                stsdict2 = Table({'白干': ['白干酒'], '白幹': ['白做'], '白乾': ['白乾杯']})
                stsdict = stsdict.join(stsdict2)
                self.assertEqual({
                    '干': ['幹', '乾', '干'],
                    '白乾': ['白乾杯'],
                    '白干': ['白做', '白干酒', '白乾杯'],
                    '白幹': ['白做']
                }, stsdict)


class TestClassStsMaker(unittest.TestCase):
    def convert_text(self, text, config, method='convert_text'):
        stsdict = StsMaker().make(config, quiet=True)
        converter = StsConverter(stsdict)
        return getattr(converter, method)(text)

    def check_case(self, subdir, name, config=None):
        dir_ = os.path.join(root_dir, subdir)

        with open(os.path.join(dir_, name + '.in'), 'r', encoding='UTF-8') as fh:
            input = fh.read()

        with open(os.path.join(dir_, name + '.ans'), 'r', encoding='UTF-8') as fh:
            answer = fh.read()

        result = self.convert_text(input, config or os.path.join(dir_, name + '.json'))
        self.assertEqual(answer, result)

    def test_merge1(self):
        self.check_case('test_make', 'merge1')

    def test_merge2(self):
        self.check_case('test_make', 'merge2')

    def test_join1(self):
        self.check_case('test_make', 'join1')

    def test_join2(self):
        self.check_case('test_make', 'join2')

    def test_join3(self):
        self.check_case('test_make', 'join3')

    def test_join4(self):
        self.check_case('test_make', 'join4')


class TestClassStsConverter(unittest.TestCase):
    def setUp(self):
        """Set up a sub temp directory for testing."""
        self.root = tempfile.mkdtemp(dir=tmpdir)

    def test_init(self):
        tempfile = os.path.join(self.root, 'test.list')
        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""干\t幹 乾 干\n干姜\t乾薑""")
        converter = StsConverter(tempfile)
        self.assertEqual({'干': ['幹', '乾', '干'], '干姜': ['乾薑']}, converter.table)

        # file as str (.jlist)
        tempfile = os.path.join(self.root, 'test.jlist')
        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""{"干": ["干", "榦"], "姜": ["姜", "薑"], "干姜": ["乾薑"]}""")
        converter = StsConverter(tempfile)
        self.assertEqual({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, converter.table)

        # file as str (.tlist)
        tempfile = os.path.join(self.root, 'test.tlist')
        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""{"干": {"": ["干", "榦"], "姜": {"": ["乾薑"]}}, "姜": {"": ["姜", "薑"]}}""")
        converter = StsConverter(tempfile)
        self.assertEqual({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, converter.table)

        # file as os.PathLike object
        tempfile = Path(os.path.join(self.root, 'test-path-like.list'))
        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""干\t幹 乾 干\n干姜\t乾薑""")
        converter = StsConverter(tempfile)
        self.assertEqual({'干': ['幹', '乾', '干'], '干姜': ['乾薑']}, converter.table)

        # StsDict
        stsdict = Trie({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        converter = StsConverter(stsdict)
        self.assertEqual({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, converter.table)

    def test_convert(self):
        stsdict = StsMaker().make('s2t', quiet=True)
        converter = StsConverter(stsdict)
        input = """干了 干涉
⿰虫风需要简转繁
⿱艹⿰虫风不需要简转繁
沙⿰虫风也简转繁"""
        expected = [(['干', '了'], ['幹了', '乾了']), ' ', (['干', '涉'], ['干涉']), '\n',
                    '⿰虫风', '需', '要', (['简'], ['簡']), (['转'], ['轉']), '繁', '\n',
                    '⿱艹⿰虫风', '不', '需', '要', (['简'], ['簡']), (['转'], ['轉']), '繁', '\n',
                    '沙', '⿰虫风', '也', (['简'], ['簡']), (['转'], ['轉']), '繁']
        self.assertEqual(expected, list(converter.convert(input)))

    def test_convert_exclude(self):
        stsdict = StsMaker().make('s2t', quiet=True)
        converter = StsConverter(stsdict)
        expected = ['尸', '廿', '山', '女', '田', (['卜'], ['卜', '蔔'])]
        output = list(converter.convert(r"""-{尸}-廿山女田卜""", re.compile(r'-{(?P<return>.*?)}-')))
        self.assertEqual(expected, output)

        stsdict = StsMaker().make('s2t', quiet=True)
        converter = StsConverter(stsdict)
        expected = [(['发', '财'], ['發財']), (['了'], ['了', '瞭']), '财', '干']
        output = list(converter.convert(r"""发财了<!-->财<--><!-->干<-->""", re.compile(r'<!-->(?P<return>.*?)<-->')))
        self.assertEqual(expected, output)

        stsdict = StsMaker().make('s2twp', quiet=True)
        converter = StsConverter(stsdict)
        expected = ['「奔馳」', '不', '是', (['奔', '馳'], ['賓士'])]
        output = list(converter.convert(r"""「奔馳」不是奔馳""", re.compile(r'「.*?」')))
        self.assertEqual(expected, output)

        stsdict = StsMaker().make('s2twp', quiet=True)
        converter = StsConverter(stsdict)
        expected = ['奔', (['驰'], ['馳'])]
        output = list(converter.convert(r"""奔-{}-驰""", re.compile(r'-{(?P<return>.*?)}-')))  # noqa: P103
        self.assertEqual(expected, output)

    def test_convert_formatted(self):
        stsdict = Trie({
            '⿰虫风': ['𧍯'],
            '沙⿰虫风': ['沙虱'],
            '干': ['幹', '乾', '干'],
            '干涉': ['干涉'],
            '会': ['會'],
            '简': ['簡'],
            '虫': ['蟲'],
            '转': ['轉'],
            '错': ['錯'],
            '风': ['風'],
        })
        converter = StsConverter(stsdict)
        input = r"""干了 干涉
⿰虫风需要简转繁
⿱艹⿰虫风不需要简转繁
沙⿰虫风也简转繁"""

        expected = r"""幹了 干涉
𧍯需要簡轉繁
⿱艹⿰虫风不需要簡轉繁
沙虱也簡轉繁"""
        output = ''.join(converter.convert_formatted(input, 'txt'))
        self.assertEqual(expected, output)

        expected = r"""{{干->幹|乾|干}}了 {{干涉}}
{{⿰虫风->𧍯}}需要{{简->簡}}{{转->轉}}繁
⿱艹⿰虫风不需要{{简->簡}}{{转->轉}}繁
{{沙⿰虫风->沙虱}}也{{简->簡}}{{转->轉}}繁"""
        output = ''.join(converter.convert_formatted(input, 'txtm'))
        self.assertEqual(expected, output)

        expected = r"""<a><del hidden>干</del><ins>幹</ins><ins hidden>乾</ins><ins hidden>干</ins></a>了 <a><del hidden>干涉</del><ins>干涉</ins></a>
<a><del hidden>⿰虫风</del><ins>𧍯</ins></a>需要<a><del hidden>简</del><ins>簡</ins></a><a><del hidden>转</del><ins>轉</ins></a>繁
⿱艹⿰虫风不需要<a><del hidden>简</del><ins>簡</ins></a><a><del hidden>转</del><ins>轉</ins></a>繁
<a><del hidden>沙⿰虫风</del><ins>沙虱</ins></a>也<a><del hidden>简</del><ins>簡</ins></a><a><del hidden>转</del><ins>轉</ins></a>繁"""  # noqa: E501
        output = ''.join(converter.convert_formatted(input, 'html'))
        self.assertEqual(expected, output)

        output = ''.join(converter.convert_formatted(input, 'htmlpage'))
        self.assertNotEqual(expected, output)
        self.assertIn(expected, output)

        expected = r"""[[["干"],["幹","乾","干"]],"了"," ",[["干","涉"],["干涉"]],"\n",[["⿰虫风"],["𧍯"]],"需","要",[["简"],["簡"]],[["转"],["轉"]],"繁","\n","⿱艹⿰虫风","不","需","要",[["简"],["簡"]],[["转"],["轉"]],"繁","\n",[["沙","⿰虫风"],["沙虱"]],"也",[["简"],["簡"]],[["转"],["轉"]],"繁"]"""  # noqa: E501
        output = ''.join(converter.convert_formatted(input, 'json'))
        self.assertEqual(expected, output)

    def test_convert_formatted_options(self):
        converter = StsConverter(Table())

        with mock.patch('sts.StsConverter.convert') as mocker:
            regex = re.compile(r'<!--(.*?)-->')
            list(converter.convert_formatted('乾柴', exclude=regex))
            mocker.assert_called_with('乾柴', exclude=regex)

    def test_convert_text(self):
        stsdict = StsMaker().make('s2t', quiet=True)
        converter = StsConverter(stsdict)
        input = """干了 干涉
⿰虫风需要简转繁
⿱艹⿰虫风不需要简转繁
沙⿰虫风也简转繁"""
        expected = r"""幹了 干涉
⿰虫风需要簡轉繁
⿱艹⿰虫风不需要簡轉繁
沙⿰虫风也簡轉繁"""
        self.assertEqual(expected, converter.convert_text(input))

    def test_convert_text_options(self):
        converter = StsConverter(Table())

        with mock.patch('sts.StsConverter.convert_formatted') as mocker:
            regex = re.compile(r'<!--(.*?)-->')
            converter.convert_text('乾柴', format='json', exclude=regex)
            mocker.assert_called_with('乾柴', format='json', exclude=regex)

        with mock.patch('sts.StsConverter.convert_formatted') as mocker:
            regex = re.compile(r'<!--(.*?)-->')
            converter.convert_text('程序', 'txtm', regex)
            mocker.assert_called_with('程序', format='txtm', exclude=regex)

    def test_convert_file(self):
        tempfile = os.path.join(self.root, 'test.tmp')
        tempfile2 = os.path.join(self.root, 'test2.tmp')

        stsdict = StsMaker().make('s2t', quiet=True)
        converter = StsConverter(stsdict)

        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""干柴烈火 发财圆梦""")
        converter.convert_file(tempfile, tempfile2)
        with open(tempfile2, 'r', encoding='UTF-8') as fh:
            result = fh.read()
        self.assertEqual("""乾柴烈火 發財圓夢""", result)

        with open(tempfile, 'w', encoding='GBK') as fh:
            fh.write("""干柴烈火 发财圆梦""")
        converter.convert_file(tempfile, tempfile2, input_encoding='GBK', output_encoding='Big5')
        with open(tempfile2, 'r', encoding='Big5') as fh:
            result = fh.read()
        self.assertEqual("""乾柴烈火 發財圓夢""", result)

    def test_convert_file_stdin(self):
        tempfile2 = os.path.join(self.root, 'test2.tmp')

        stsdict = StsMaker().make('s2t', quiet=True)
        converter = StsConverter(stsdict)

        with mock.patch('sys.stdin', io.StringIO("""干柴烈火 发财圆梦""")):
            converter.convert_file(None, tempfile2)
        with open(tempfile2, 'r', encoding='UTF-8') as fh:
            result = fh.read()
        self.assertEqual("""乾柴烈火 發財圓夢""", result)

    def test_convert_file_stdout(self):
        tempfile = os.path.join(self.root, 'test.tmp')

        stsdict = StsMaker().make('s2t', quiet=True)
        converter = StsConverter(stsdict)

        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""干柴烈火 发财圆梦""")

        with redirect_stdout(io.StringIO()) as fh:
            converter.convert_file(tempfile)

        self.assertEqual("""乾柴烈火 發財圓夢""", fh.getvalue())

    def test_convert_file_options(self):
        converter = StsConverter(Table())

        with mock.patch('sts.StsConverter.convert_formatted') as mocker, \
             mock.patch('sys.stdin', io.StringIO('干姜')):
            regex = re.compile(r'<!--(.*?)-->')
            converter.convert_file(None, format='html', exclude=regex)
            mocker.assert_called_with('干姜', format='html', exclude=regex)


class TestBasicCases(unittest.TestCase):
    def test_ids(self):
        stsdict = Trie({
            '会': ['會'],
            '简': ['簡'],
            '虫': ['蟲'],
            '转': ['轉'],
            '错': ['錯'],
            '风': ['風'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual('⿰虫风簡轉繁不會出錯', converter.convert_text('⿰虫风简转繁不会出错'))
        self.assertEqual('⿱艹⿰虫风簡轉繁不會出錯', converter.convert_text('⿱艹⿰虫风简转繁不会出错'))

        stsdict = Trie({
            '⿰虫风': ['𧍯'],
            '会': ['會'],
            '简': ['簡'],
            '虫': ['蟲'],
            '转': ['轉'],
            '错': ['錯'],
            '风': ['風'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual('𧍯需要簡轉繁', converter.convert_text('⿰虫风需要简转繁'))
        self.assertEqual('⿱艹⿰虫风不需要簡轉繁', converter.convert_text('⿱艹⿰虫风不需要简转繁'))

        stsdict = Trie({
            '⿱艹⿰虫风': ['⿱艹𧍯'],
            '会': ['會'],
            '简': ['簡'],
            '虫': ['蟲'],
            '转': ['轉'],
            '错': ['錯'],
            '风': ['風'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual('⿰虫风不需要簡轉繁', converter.convert_text('⿰虫风不需要简转繁'))
        self.assertEqual('⿱艹𧍯需要簡轉繁', converter.convert_text('⿱艹⿰虫风需要简转繁'))

    def test_ids_broken(self):
        stsdict = StsMaker().make('tw2s', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual('IDC有这些：⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻，接着繁转简', converter.convert_text('IDC有這些：⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻，接著繁轉簡'))
        self.assertEqual('「⿰⿱⿲⿳」不影响后面', converter.convert_text('「⿰⿱⿲⿳」不影響後面'))
        self.assertEqual('⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻長度不夠\n这行无影响', converter.convert_text('⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻長度不夠\n這行無影響'))

    def test_vi(self):
        stsdict = Trie({
            '劍': ['剑'],
            '〾劍': ['剑'],
            '訢': ['欣', '䜣'],
            '劍訢': ['剑䜣'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual('刀剑 剑䜣', converter.convert_text('刀劍 劍訢'))
        self.assertEqual('刀剑 剑欣 剑〾訢 剑〾訢', converter.convert_text('刀〾劍 〾劍訢 劍〾訢 〾劍〾訢'))

    def test_vs(self):
        stsdict = Trie({
            '劍': ['剑'],
            '劍󠄁': ['剑'],
            '訢': ['欣', '䜣'],
            '劍訢': ['剑䜣'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual('刀剑 剑䜣', converter.convert_text('刀劍 劍訢'))
        self.assertEqual('刀剑 剑欣', converter.convert_text('刀劍󠄁 劍󠄁訢'))
        self.assertEqual('刀劍󠄃 劍󠄃欣', converter.convert_text('刀劍󠄃 劍󠄃訢'))
        self.assertEqual('刀劍󠄁󠄂 劍󠄁󠄂欣', converter.convert_text('刀劍󠄁󠄂 劍󠄁󠄂訢'))

    def test_cdm(self):
        stsdict = Trie({
            '黑桃A': ['葵扇A'],
            '黑桃Å': ['扇子Å'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual('出葵扇A', converter.convert_text('出黑桃A'))
        self.assertEqual('出扇子Å', converter.convert_text('出黑桃Å'))
        self.assertEqual('出黑桃A̧', converter.convert_text('出黑桃A̧'))
        self.assertEqual('出黑桃Å̧', converter.convert_text('出黑桃Å̧'))

        stsdict = Trie({
            'A片': ['成人片'],
            'Å片': ['特製成人片'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual('看成人片', converter.convert_text('看A片'))
        self.assertEqual('看特製成人片', converter.convert_text('看Å片'))
        self.assertEqual('看A̧片', converter.convert_text('看A̧片'))
        self.assertEqual('看Å̧片', converter.convert_text('看Å̧片'))


class TestConfigs(unittest.TestCase):
    @slow_test()
    def test_make(self):
        def clear_lists():
            pattern = re.compile(r'\.(?:[jt]?list)$', re.I)
            with os.scandir(config_dir) as it:
                for file in it:
                    if pattern.search(file.path):
                        os.remove(file)

        config_dir = StsMaker.DEFAULT_CONFIG_DIR
        maker = StsMaker()
        pattern = re.compile(r'\.json$', re.I)
        for file in os.listdir(config_dir):
            if pattern.search(file):
                with self.subTest(config=file):
                    clear_lists()
                    maker.make(file, quiet=True)


if __name__ == '__main__':
    unittest.main()
