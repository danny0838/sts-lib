import io
import itertools
import json
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from textwrap import dedent
from unittest import mock

import yaml

from sts import (
    StreamList,
    StsConverter,
    StsDict,
    StsMaker,
    Table,
    Trie,
    Unicode,
)
from sts import __version__ as sts_version

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


class TestStreamList(unittest.TestCase):
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


class TestUnicode(unittest.TestCase):
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


class TestStsDict(unittest.TestCase):
    def setUp(self):
        """Set up a sub temp directory for testing."""
        self.root = tempfile.mkdtemp(dir=tmpdir)

    def test_init(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
                self.assertEqual({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, stsdict)

                stsdict = cls(StsDict({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}))
                self.assertEqual(StsDict({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}), stsdict)

                stsdict = cls([('干', ['幹', '乾', '干']), ('姜', ['姜', '薑']), ('干姜', ['乾薑'])])
                self.assertEqual({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, stsdict)

                stsdict = cls(干=['幹', '乾', '干'], 姜=['姜', '薑'], 干姜=['乾薑'])
                self.assertEqual({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, stsdict)

    def test_repr(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
                self.assertEqual(stsdict, eval(repr(stsdict)))

    def test_getitem(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干': ['幹', '乾', '干'], '豆干': ['豆乾']})
                self.assertEqual(['幹', '乾', '干'], stsdict['干'])
                self.assertEqual(['豆乾'], stsdict['豆干'])
                with self.assertRaises(KeyError):
                    stsdict['豆']
                with self.assertRaises(KeyError):
                    stsdict['豆乾']

    def test_contains(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干': ['幹', '乾', '干'], '豆干': ['豆乾']})
                self.assertTrue('干' in stsdict)
                self.assertTrue('豆干' in stsdict)
                self.assertFalse('豆' in stsdict)
                self.assertFalse('豆乾' in stsdict)

    def test_len(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls()
                self.assertEqual(0, len(stsdict))

                stsdict = cls({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
                self.assertEqual(3, len(stsdict))

    def test_iter(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干': ['幹', '乾', '干'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
                self.assertEqual({'干', '姜', '干姜'}, set(stsdict))

    def test_eq(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
                stsdict = cls(dict_)
                self.assertTrue(stsdict == dict_)
                self.assertTrue(dict_ == stsdict)
                self.assertFalse(stsdict != dict_)
                self.assertFalse(dict_ != stsdict)

                dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
                dict2 = {'干姜': ['乾薑'], '干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
                stsdict = cls(dict_)
                self.assertTrue(stsdict == dict2)
                self.assertTrue(dict2 == stsdict)
                self.assertFalse(stsdict != dict2)
                self.assertFalse(dict2 != stsdict)

                dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
                dict2 = {'干姜': ['乾薑'], '干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
                stsdict = cls(dict_)
                stsdict2 = cls(dict2)
                self.assertTrue(stsdict == stsdict2)
                self.assertTrue(stsdict2 == stsdict)
                self.assertFalse(stsdict != stsdict2)
                self.assertFalse(stsdict2 != stsdict)

                dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
                dict2 = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
                stsdict = cls(dict_)
                self.assertFalse(stsdict == dict2)
                self.assertFalse(dict2 == stsdict)
                self.assertTrue(stsdict != dict2)
                self.assertTrue(dict2 != stsdict)

                dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
                dict2 = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
                stsdict = cls(dict_)
                self.assertFalse(stsdict == dict2)
                self.assertFalse(dict2 == stsdict)
                self.assertTrue(stsdict != dict2)
                self.assertTrue(dict2 != stsdict)

                dict_ = {'干': ['幹', '乾', '干', '𠏉'], '姜': ['姜', '薑']}
                dict2 = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
                stsdict = cls(dict_)
                self.assertFalse(stsdict == dict2)
                self.assertFalse(dict2 == stsdict)
                self.assertTrue(stsdict != dict2)
                self.assertTrue(dict2 != stsdict)

    def test_delitem(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干姜': ['乾薑'], '姜': ['姜', '薑']})
                del stsdict['干姜']
                self.assertEqual({'姜'}, set(stsdict))

                stsdict = cls({'干姜': ['乾薑'], '姜': ['姜', '薑']})
                with self.assertRaises(KeyError):
                    del stsdict['干']

    def test_keys(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干': ['幹', '乾', '干'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
                self.assertEqual({'干', '姜', '干姜'}, set(stsdict.keys()))

    def test_values(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干': ['幹', '乾', '干'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
                self.assertEqual({('幹', '乾', '干'), ('姜', '薑'), ('乾薑',)}, {tuple(x) for x in stsdict.values()})

    def test_items(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
                self.assertEqual({'干': ['幹', '乾'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, dict(stsdict.items()))

    def test_add(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                # str
                stsdict = cls()

                stsdict.add('干', '幹')
                self.assertEqual({'干': ['幹']}, stsdict)

                stsdict.add('干', '乾')
                self.assertEqual({'干': ['幹', '乾']}, stsdict)

                stsdict.add('姜', '姜')
                self.assertEqual({'干': ['幹', '乾'], '姜': ['姜']}, stsdict)

                # list
                stsdict = cls()

                stsdict.add('干', ['幹', '乾'])
                self.assertEqual({'干': ['幹', '乾']}, stsdict)

                stsdict.add('干', '干')
                self.assertEqual({'干': ['幹', '乾', '干']}, stsdict)

                stsdict.add('干', ['榦'])
                self.assertEqual({'干': ['幹', '乾', '干', '榦']}, stsdict)

                stsdict.add('姜', ['姜', '薑'])
                self.assertEqual({'干': ['幹', '乾', '干', '榦'], '姜': ['姜', '薑']}, stsdict)

                # iterable
                stsdict = cls()

                stsdict.add('干', ('幹', '乾'))
                self.assertEqual({'干': ['幹', '乾']}, stsdict)

                stsdict.add('干', iter(('幹', '乾', '干')))
                self.assertEqual({'干': ['幹', '乾', '干']}, stsdict)

    def test_add_skip_check(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                # list
                stsdict = cls({'干': ['幹', '乾']})

                stsdict.add('干', ['乾'])
                self.assertEqual({'干': ['幹', '乾']}, stsdict)

                stsdict.add('干', ['乾'], skip_check=True)
                self.assertEqual({'干': ['幹', '乾', '乾']}, stsdict)

                # iterable
                stsdict = cls()

                stsdict.add('干', ('幹', '乾'), skip_check=True)
                self.assertEqual({'干': ['幹', '乾']}, stsdict)

                stsdict.add('干', iter(('幹', '乾')), skip_check=True)
                self.assertEqual({'干': ['幹', '乾', '幹', '乾']}, stsdict)

    def test_update(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干': ['幹', '乾']})

                dict_ = StsDict({'干': ['干'], '姜': ['姜', '薑']})
                stsdict.update(dict_)
                self.assertEqual({'干': ['幹', '乾', '干'], '姜': ['姜', '薑']}, stsdict)

                dict_ = {'干': ['干', '榦'], '干姜': ['乾薑']}
                stsdict.update(dict_)
                self.assertEqual({'干': ['幹', '乾', '干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, stsdict)

    def test_load_plain(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                tempfile = os.path.join(self.root, 'test.tmp')
                tempfile2 = os.path.join(self.root, 'test2.tmp')

                with open(tempfile, 'w', encoding='UTF-8') as fh:
                    fh.write("""干\t幹 乾""")
                with open(tempfile2, 'w', encoding='UTF-8') as fh:
                    fh.write("""干\t干 榦\n姜\t姜 薑""")

                stsdict = cls()
                stsdict.load(tempfile)
                stsdict.load(tempfile2)
                self.assertEqual({'干': ['幹', '乾', '干', '榦'], '姜': ['姜', '薑']}, stsdict)

                # trailing linefeed
                with open(tempfile, 'w', encoding='UTF-8') as fh:
                    fh.write("""干\t幹\n""")

                stsdict = cls()
                stsdict.load(tempfile)
                self.assertEqual({'干': ['幹']}, stsdict)

                # empty value
                with open(tempfile, 'w', encoding='UTF-8') as fh:
                    fh.write("""干\t""")

                stsdict = cls()
                stsdict.load(tempfile)
                self.assertEqual({'干': ['']}, stsdict)

                # empty line (error in OpenCC < 1.1.4)
                with open(tempfile, 'w', encoding='UTF-8') as fh:
                    fh.write("""干\t幹\n\n于\t於""")

                stsdict = cls()
                stsdict.load(tempfile)
                self.assertEqual({'干': ['幹'], '于': ['於']}, stsdict)

                with open(tempfile, 'w', encoding='UTF-8') as fh:
                    fh.write("""干\t幹\n\n""")

                stsdict = cls()
                stsdict.load(tempfile)
                self.assertEqual({'干': ['幹']}, stsdict)

                # 0 tab: output same (error in OpenCC)
                with open(tempfile, 'w', encoding='UTF-8') as fh:
                    fh.write("""干\n于""")

                stsdict = cls()
                stsdict.load(tempfile)
                self.assertEqual({'干': ['干'], '于': ['于']}, stsdict)

                # 2 tabs: safely ignored (2nd tab treated as part of value in OpenCC)
                with open(tempfile, 'w', encoding='UTF-8') as fh:
                    fh.write("""干\t幹 乾\t# 一些註解""")

                stsdict = cls()
                stsdict.load(tempfile)
                self.assertEqual({'干': ['幹', '乾']}, stsdict)

    def test_load_json(self):
        for cls, ext in itertools.product((StsDict, Table, Trie), ('json', 'jlist')):
            with self.subTest(type=cls, ext=ext):
                tempfile = os.path.join(self.root, f'test.{ext}')
                tempfile2 = os.path.join(self.root, f'test2.{ext}')

                # dict as {key1: values1, ...} or [[key1, values1], [key2, values2], ...]
                # where values is a str or a list of strs
                with open(tempfile, 'w', encoding='UTF-8') as fh:
                    json.dump({'简': '簡', '干': ['幹', '乾']}, fh)
                with open(tempfile2, 'w', encoding='UTF-8') as fh:
                    json.dump([['干', ['干', '榦']], ['姜', ['姜', '薑']], ['体', '體']], fh)

                stsdict = cls()
                stsdict.load(tempfile)
                stsdict.load(tempfile2)
                self.assertEqual({
                    '简': ['簡'],
                    '干': ['幹', '乾', '干', '榦'],
                    '姜': ['姜', '薑'],
                    '体': ['體'],
                }, stsdict)

    def test_load_yaml(self):
        for cls, ext in itertools.product((StsDict, Table, Trie), ('yaml', 'yml')):
            with self.subTest(type=cls, ext=ext):
                tempfile = os.path.join(self.root, f'test.{ext}')
                tempfile2 = os.path.join(self.root, f'test2.{ext}')

                # dict as {key1: values1, ...} or [[key1, values1], [key2, values2], ...]
                # where values is a str or a list of strs
                with open(tempfile, 'w', encoding='UTF-8') as fh:
                    yaml.dump(
                        {'简': '簡', '干': ['幹', '乾']},
                        fh, allow_unicode=True,
                    )
                with open(tempfile2, 'w', encoding='UTF-8') as fh:
                    yaml.dump(
                        [['干', ['干', '榦']], ['姜', ['姜', '薑']], ['体', '體']],
                        fh, allow_unicode=True,
                    )

                stsdict = cls()
                stsdict.load(tempfile)
                stsdict.load(tempfile2)
                self.assertEqual({
                    '简': ['簡'],
                    '干': ['幹', '乾', '干', '榦'],
                    '姜': ['姜', '薑'],
                    '体': ['體'],
                }, stsdict)

    def test_load_type(self):
        """Forced with type parameter"""
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                # .json load as plain
                tempfile = os.path.join(self.root, 'test.json')
                with open(tempfile, 'w', encoding='UTF-8') as fh:
                    fh.write("""干\t幹 乾""")

                stsdict = cls()
                stsdict.load(tempfile, type='txt')
                self.assertEqual({'干': ['幹', '乾']}, stsdict)

                # .txt load as json
                tempfile = os.path.join(self.root, 'test.txt')
                with open(tempfile, 'w', encoding='UTF-8') as fh:
                    json.dump({'干': ['幹', '乾']}, fh)

                stsdict = cls()
                stsdict.load(tempfile, type='json')
                self.assertEqual({'干': ['幹', '乾']}, stsdict)

    def test_dump(self):
        tempfile = os.path.join(self.root, 'test.tmp')
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干': ['干', '榦'], '姜': ['姜', '薑']})

                stsdict.dump(tempfile)
                with open(tempfile, 'r', encoding='UTF-8') as fh:
                    text = fh.read()
                self.assertEqual('干\t干 榦\n姜\t姜 薑\n', text)

                stsdict.dump(tempfile, sort=True)
                with open(tempfile, 'r', encoding='UTF-8') as fh:
                    text = fh.read()
                self.assertEqual('姜\t姜 薑\n干\t干 榦\n', text)

    def test_dump_stdout(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干': ['干', '榦'], '姜': ['姜', '薑']})
                with redirect_stdout(io.StringIO()) as fh:
                    stsdict.dump()
                self.assertEqual('干\t干 榦\n姜\t姜 薑\n', fh.getvalue())

    def test_dump_badchar(self):
        tempfile = os.path.join(self.root, 'test.tmp')
        for cls in (StsDict, Table, Trie):
            for badchar in '\t\n\r':
                with self.subTest(type=cls, char=badchar, where='key'):
                    stsdict = cls({f'干{badchar}姜': ['乾薑']})

                    # check if an error is raised when check=True
                    with self.assertRaises(ValueError):
                        stsdict.dump(tempfile, check=True)

                    # check if badchar really causes bad loading
                    stsdict.dump(tempfile)
                    stsdict2 = cls()
                    stsdict2.load(tempfile)
                    self.assertNotEqual(stsdict, stsdict2)

            for badchar in ' \t\n\r':
                with self.subTest(type=cls, char=badchar, where='value'):
                    stsdict = cls({'干姜': [f'乾{badchar}薑']})

                    # check if an error is raised when check=True
                    with self.assertRaises(ValueError):
                        stsdict.dump(tempfile, check=True)

                    # check if badchar really causes bad loading
                    stsdict.dump(tempfile)
                    stsdict2 = cls()
                    stsdict2.load(tempfile)
                    self.assertNotEqual(stsdict, stsdict2)

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
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
                self.assertIsNone(stsdict.match('吃干姜了', 0))
                self.assertEqual(((['干', '姜'], ['乾薑']), 1, 3), stsdict.match('吃干姜了', 1))
                self.assertEqual(((['姜'], ['姜', '薑']), 2, 3), stsdict.match('吃干姜了', 2))
                self.assertIsNone(stsdict.match('吃干姜了', 3))

                # treat empty values as no match
                stsdict = cls({'需': []})
                self.assertIsNone(stsdict.match('需要', 0))

    def test_apply(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
                self.assertEqual(['吃', (['干', '姜'], ['乾薑']), '了'], list(stsdict.apply('吃干姜了')))

    def test_apply_enum(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'钟': ['鐘', '鍾'], '药': ['藥', '葯'], '用药': ['用藥']})
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
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'采信': ['採信'], '信息': ['訊息']})
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
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'註冊表': ['登錄檔']})
                stsdict2 = Table({'注': ['註', '注']})
                stsdict = stsdict._join_prefix(stsdict2)
                self.assertEqual({'注冊表': ['登錄檔'], '註冊表': ['登錄檔']}, stsdict)

                stsdict = cls({'註冊表': ['登錄檔']})
                stsdict2 = Table({'注': ['注', '註']})
                stsdict = stsdict._join_prefix(stsdict2)
                self.assertEqual({'注冊表': ['注冊表', '登錄檔'], '註冊表': ['登錄檔']}, dict(stsdict))

                stsdict = cls({'注冊表': [], '註冊表': ['登錄檔']})
                stsdict2 = Table({'注': ['注', '註']})
                stsdict = stsdict._join_prefix(stsdict2)
                self.assertEqual({'注冊表': ['注冊表', '登錄檔'], '註冊表': ['登錄檔']}, stsdict)

                stsdict = cls({'註冊表': ['登錄檔']})
                stsdict2 = Table({'注': ['注', '註'], '册': ['冊'], '注册': ['註冊']})
                stsdict = stsdict._join_prefix(stsdict2)
                self.assertEqual({'注册表': ['登錄檔'], '註冊表': ['登錄檔'], '註册表': ['登錄檔'], '注冊表': ['注冊表', '登錄檔']}, stsdict)

    def test_postfix(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'因为': ['因爲']})
                stsdict2 = Table({'爲': ['為']})
                stsdict = stsdict._join_postfix(stsdict2)
                self.assertEqual({'因为': ['因為'], '爲': ['為']}, stsdict)

    def test_join(self):
        for cls in (StsDict, Table, Trie):
            with self.subTest(type=cls):
                stsdict = cls({'则': ['則'], '达': ['達'], '规': ['規']})
                stsdict2 = Table({'正則表達式': ['正規表示式'], '表達式': ['表示式']})
                stsdict = stsdict.join(stsdict2)
                self.assertEqual({
                    '则': ['則'], '达': ['達'], '规': ['規'],
                    '正則表達式': ['正規表示式'], '表達式': ['表示式'],
                    '正则表达式': ['正規表示式'], '正则表達式': ['正規表示式'], '正則表达式': ['正規表示式'],
                    '表达式': ['表示式'],
                }, stsdict)

                stsdict = cls({
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

                stsdict = cls({'妳': ['你', '奶']})
                stsdict2 = Table({'奶媽': ['奶娘']})
                stsdict = stsdict.join(stsdict2)
                self.assertEqual({
                    '妳': ['你', '奶'],
                    '奶媽': ['奶娘'],
                    '妳媽': ['妳媽', '奶娘'],
                }, stsdict)

                stsdict = cls({'汇': ['匯', '彙'], '编': ['編'], '汇编': ['彙編']})
                stsdict2 = Table({'彙編': ['組譯']})
                stsdict = stsdict.join(stsdict2)
                self.assertEqual({
                    '彙編': ['組譯'], '彙编': ['組譯'], '汇': ['匯', '彙'],
                    '汇編': ['汇編', '組譯'], '汇编': ['組譯'], '编': ['編'],
                }, stsdict)

                stsdict = cls({'干': ['幹', '乾', '干'], '白干': ['白幹', '白干']})
                stsdict2 = Table({'白干': ['白干酒'], '白幹': ['白做'], '白乾': ['白乾杯']})
                stsdict = stsdict.join(stsdict2)
                self.assertEqual({
                    '干': ['幹', '乾', '干'],
                    '白乾': ['白乾杯'],
                    '白干': ['白做', '白干酒', '白乾杯'],
                    '白幹': ['白做']
                }, stsdict)


class TestTable(unittest.TestCase):
    def test_key_map_basic(self):
        # basic
        stsdict = Table({
            '干': ['幹', '乾'],
            '干姜': ['乾薑'],
            '干不下': ['幹不下'],
            '干不了': ['幹不了'],
            '姜': ['姜', '薑'],
        })
        self.assertEqual({'干姜': 2, '干不': 3}, stsdict.key_map)

        stsdict = Table({
            '干不干净': ['乾不乾淨'],
            '干': ['幹', '乾'],
            '干姜': ['乾薑'],
            '干不下': ['幹不下'],
            '干不了': ['幹不了'],
        })
        self.assertEqual({'干不': 4, '干姜': 2}, stsdict.key_map)

        # IDS
        stsdict = Table({'⿰虫风': ['𧍯'], '沙⿰虫风': ['沙虱']})
        self.assertEqual({'沙⿰虫风': 2}, stsdict.key_map)

    def test_key_map_cache(self):
        # getter
        stsdict = Table({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
        dict_ = stsdict.key_map
        self.assertEqual({'干姜': 2}, dict_)
        self.assertIs(dict_, stsdict.key_map)

        # setter
        stsdict.key_map = {'干不': 3}
        self.assertEqual({'干不': 3}, stsdict.key_map)

        # deleter
        stsdict.add('了', ['了', '瞭'])
        stsdict.add('不了解', ['不瞭解'])
        del stsdict.key_map
        self.assertEqual({'干姜': 2, '不了': 3}, stsdict.key_map)


class TestStsMaker(unittest.TestCase):
    def setUp(self):
        """Set up a sub temp directory for testing."""
        self.root = tempfile.mkdtemp(dir=tmpdir)

    def test_bad_config_object(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump([], fh)

        with self.assertRaises(ValueError):
            StsMaker().make(config_file, quiet=True)

    def test_no_dicts(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({}, fh)

        with self.assertRaises(ValueError):
            StsMaker().make(config_file, quiet=True)

    def test_dict_str(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    'dict.txt',
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干姜\t乾薑
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        self.assertEqual(os.path.join(self.root, 'dict.txt'), stsdict)

    def test_dict_str_missing_file(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    'dict.txt',
                ],
            }, fh)

        with self.assertRaises(RuntimeError):
            StsMaker().make(config_file, quiet=True)

    def test_dict_no_file(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'mode': 'load',
                        'src': [
                            'dict.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干姜\t乾薑
                """
            ))

        with self.assertRaises(RuntimeError):
            StsMaker().make(config_file, quiet=True)

    def test_dict_no_src(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.txt',
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干姜\t乾薑
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        self.assertEqual(os.path.join(self.root, 'dict.txt'), stsdict)

    def test_dict_no_src_and_file_nonexist(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.txt',
                    },
                ],
            }, fh)

        with self.assertRaises(RuntimeError):
            StsMaker().make(config_file, quiet=True)

    def test_dict_src_nested(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.txt',
                        'mode': 'swap',
                        'src': [
                            {
                                'mode': 'load',
                                'src': [
                                    'phrases.txt',
                                    'chars.txt',
                                ],
                            },
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'phrases.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干你娘\t幹你娘
                """
            ))

        with open(os.path.join(self.root, 'chars.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干\t幹 乾 干
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '幹你娘': ['干你娘'],
            '幹': ['干'],
            '乾': ['干'],
            '干': ['干'],
        }, dict(converter.table))

    def test_dict_format_list(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'load',
                        'src': [
                            'phrases.txt',
                            'chars.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'phrases.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干姜\t乾薑
                """
            ))

        with open(os.path.join(self.root, 'chars.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                姜\t薑
                干\t幹 乾 干
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        self.assertEqual(os.path.join(self.root, 'dict.list'), stsdict)
        with open(stsdict, encoding='UTF-8') as fh:
            self.assertEqual(
                '干姜\t乾薑\n姜\t薑\n干\t幹 乾 干\n',
                fh.read()
            )

    def test_dict_format_jlist(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.jlist',
                        'mode': 'load',
                        'src': [
                            'phrases.txt',
                            'chars.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'phrases.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干姜\t乾薑
                """
            ))

        with open(os.path.join(self.root, 'chars.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                姜\t薑
                干\t幹 乾 干
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        self.assertEqual(os.path.join(self.root, 'dict.jlist'), stsdict)
        with open(stsdict, encoding='UTF-8') as fh:
            self.assertEqual(
                '{"干姜":["乾薑"],"姜":["薑"],"干":["幹","乾","干"]}',
                fh.read()
            )

    def test_dict_format_tlist(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.tlist',
                        'mode': 'load',
                        'src': [
                            'phrases.txt',
                            'chars.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'phrases.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干姜\t乾薑
                """
            ))

        with open(os.path.join(self.root, 'chars.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                姜\t薑
                干\t幹 乾 干
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        self.assertEqual(os.path.join(self.root, 'dict.tlist'), stsdict)
        with open(stsdict, encoding='UTF-8') as fh:
            self.assertEqual(
                '{"干":{"姜":{"":["乾薑"]},"":["幹","乾","干"]},"姜":{"":["薑"]}}',
                fh.read()
            )

    def test_dict_format_other(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.txt',
                        'mode': 'load',
                        'src': [
                            'phrases.txt',
                            'chars.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'phrases.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干姜\t乾薑
                """
            ))

        with open(os.path.join(self.root, 'chars.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                姜\t薑
                干\t幹 乾 干
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        self.assertEqual(os.path.join(self.root, 'dict.txt'), stsdict)
        with open(stsdict, encoding='UTF-8') as fh:
            self.assertEqual(
                '干姜\t乾薑\n姜\t薑\n干\t幹 乾 干\n',
                fh.read()
            )

    def test_dict_mode_load1(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'load',
                        'src': [
                            'phrases.txt',
                            'chars.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'phrases.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干你娘\t幹你娘
                干姜\t乾薑
                干娘\t乾娘
                """
            ))

        with open(os.path.join(self.root, 'chars.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                姜\t薑
                干\t幹 乾 干
                贵\t貴
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '干你娘': ['幹你娘'],
            '干姜': ['乾薑'],
            '干娘': ['乾娘'],
            '姜': ['薑'],
            '干': ['幹', '乾', '干'],
            '贵': ['貴'],
        }, dict(converter.table))

    def test_dict_mode_load2(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'load',
                        'src': [
                            'chars.txt',
                            'phrases.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'chars.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                姜\t薑
                干\t幹 乾 干
                贵\t貴
                """
            ))

        with open(os.path.join(self.root, 'phrases.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干你娘\t幹你娘
                干姜\t乾薑
                干娘\t乾娘
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '姜': ['薑'],
            '干': ['幹', '乾', '干'],
            '贵': ['貴'],
            '干你娘': ['幹你娘'],
            '干姜': ['乾薑'],
            '干娘': ['乾娘'],
        }, dict(converter.table))

    def test_dict_mode_swap(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'swap',
                        'src': [
                            'phrases.txt',
                            'chars.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'phrases.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干你娘\t幹你娘
                干姜\t乾薑
                干娘\t乾娘
                """
            ))

        with open(os.path.join(self.root, 'chars.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                姜\t薑
                干\t幹 乾 干
                贵\t貴
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '幹你娘': ['干你娘'],
            '乾薑': ['干姜'],
            '乾娘': ['干娘'],
            '薑': ['姜'],
            '幹': ['干'],
            '乾': ['干'],
            '干': ['干'],
            '貴': ['贵'],
        }, dict(converter.table))

    def test_dict_mode_join1(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'join',
                        'src': [
                            's2t.txt',
                            't2tw.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 's2t.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                开\t開
                碱\t鹼
                胆\t膽
                驰\t馳
                锿\t鎄
                """
            ))

        with open(os.path.join(self.root, 't2tw.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                奔馳\t賓士
                酰\t醯
                鎄\t鑀
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '开': ['開'],
            '碱': ['鹼'],
            '胆': ['膽'],
            '驰': ['馳'],
            '锿': ['鑀'],
            '奔馳': ['賓士'],
            '酰': ['醯'],
            '鎄': ['鑀'],
            '奔驰': ['賓士'],
        }, dict(converter.table))

    def test_dict_mode_join2(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'join',
                        'src': [
                            's2t.txt',
                            't2tw.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 's2t.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                表\t表 錶
                规\t規
                则\t則
                达\t達
                运\t運
                表达\t表達
                表达式\t表達式
                """
            ))

        with open(os.path.join(self.root, 't2tw.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                表達式\t表示式 運算式
                正則表達式\t正規表示式
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        self.assertEqual(os.path.join(self.root, 'dict.list'), stsdict)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '表': ['表', '錶'],
            '规': ['規'],
            '则': ['則'],
            '达': ['達'],
            '运': ['運'],
            '表达': ['表達'],
            '表达式': ['表示式', '運算式'],
            '表達式': ['表示式', '運算式'],
            '正則表達式': ['正規表示式'],
            '正则表达式': ['正規表示式'],
            '正则表達式': ['正規表示式'],
            '正則表达式': ['正規表示式'],
        }, dict(converter.table))

    def test_dict_mode_join3(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'join',
                        'src': [
                            'tw2t.txt',
                            't2s.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'tw2t.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                表示式\t表達式
                運算式\t表達式
                正規表示式\t正則表達式
                """
            ))

        with open(os.path.join(self.root, 't2s.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                規\t规
                則\t则
                達\t达
                運\t运
                表達\t表达
                表達式\t表达式
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '表示式': ['表达式'],
            '運算式': ['表达式'],
            '正規表示式': ['正则表达式'],
            '規': ['规'],
            '則': ['则'],
            '達': ['达'],
            '運': ['运'],
            '表達': ['表达'],
            '表達式': ['表达式'],
        }, dict(converter.table))

    def test_dict_mode_join4(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'join',
                        'src': [
                            's2t.txt',
                            't2tw.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 's2t.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                采\t採
                采信\t採信
                """
            ))

        with open(os.path.join(self.root, 't2tw.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                信息\t資訊
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '采': ['採'],
            '采信': ['採信'],
            '信息': ['資訊'],
        }, dict(converter.table))

    def test_dict_mode_expand(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'expand',
                        'src': [
                            'dict.txt',
                            'num1.txt',
                            'num2.txt',
                        ],
                        'placeholders': [
                            '%n',
                            '%s',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                %n里%s\t%n里%s
                """
            ))

        with open(os.path.join(self.root, 'num1.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                １\t１
                ２\t２
                """
            ))

        with open(os.path.join(self.root, 'num2.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                壹\t壹
                貳\t贰
                叄\t叁
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '１里壹': ['１里壹'],
            '１里貳': ['１里贰'],
            '１里叄': ['１里叁'],
            '２里壹': ['２里壹'],
            '２里貳': ['２里贰'],
            '２里叄': ['２里叁'],
        }, dict(converter.table))

    def test_dict_mode_expand_skipped_placeholder(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'expand',
                        'src': [
                            'dict.txt',
                            'num1.txt',
                            'num2.txt',
                        ],
                        'placeholders': [
                            '%n',
                            '%s',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                %s里\t%s里
                """
            ))

        with open(os.path.join(self.root, 'num1.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                １\t１
                ２\t２
                """
            ))

        with open(os.path.join(self.root, 'num2.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                壹\t壹
                貳\t贰
                叄\t叁
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '壹里': ['壹里'],
            '貳里': ['贰里'],
            '叄里': ['叁里'],
        }, dict(converter.table))

    def test_dict_mode_expand_no_placeholder(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'expand',
                        'src': [
                            'dict.txt',
                            'num1.txt',
                        ],
                        'placeholders': [
                            '%n',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                里\t裏 里
                """
            ))

        with open(os.path.join(self.root, 'num1.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                １\t１
                ２\t２
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '里': ['裏', '里'],
        }, dict(converter.table))

    def test_dict_mode_expand_match_same_key(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'expand',
                        'src': [
                            'dict.txt',
                            'num.txt',
                        ],
                        'placeholders': [
                            '%n',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                %n里%n\t%n里%n
                """
            ))

        with open(os.path.join(self.root, 'num.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                １\t１
                ２\t２
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '１里１': ['１里１'],
            '２里２': ['２里２'],
        }, dict(converter.table))

    def test_dict_mode_expand_in_values(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'expand',
                        'src': [
                            'dict.txt',
                            'num.txt',
                        ],
                        'placeholders': [
                            '%n',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                Ｎ里\t%n里
                """
            ))

        with open(os.path.join(self.root, 'num.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                １\t１
                ２\t２
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            'Ｎ里': ['１里', '２里'],
        }, dict(converter.table))

    def test_dict_mode_expand_multi_values(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'expand',
                        'src': [
                            'dict.txt',
                            'num.txt',
                        ],
                        'placeholders': [
                            '%n',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                %n周\t%n周 %n週
                """
            ))

        with open(os.path.join(self.root, 'num.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                １\t一 壹
                ２\t二 贰
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '１周': ['一周', '壹周', '一週', '壹週'],
            '２周': ['二周', '贰周', '二週', '贰週'],
        }, dict(converter.table))

    def test_dict_mode_expand_ids(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'expand',
                        'src': [
                            'dict.txt',
                            'expander.txt',
                        ],
                        'placeholders': [
                            '⿰虫单',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                ⿰虫单\t蟬
                ⿱艹⿰虫单\t⿱艹蟬
                """
            ))

        with open(os.path.join(self.root, 'expander.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                １\t１
                ２\t２
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '１': ['蟬'],
            '２': ['蟬'],
            '⿱艹⿰虫单': ['⿱艹蟬'],
        }, dict(converter.table))

    def test_dict_mode_filter_include_basic(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'filter',
                        'include': r'^[\u0000-\uFFFF]*$',
                        'src': [
                            'dict.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                㑮陣\t𫝈阵
                陣\t阵
                㑮\t𫝈
                噹\t当 𰁸
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        self.assertEqual(os.path.join(self.root, 'dict.list'), stsdict)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '陣': ['阵'],
            '噹': ['当'],
        }, dict(converter.table))

    def test_dict_mode_filter_include_bad_regex(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'filter',
                        'include': r'???',
                        'src': [
                            'dict.txt',
                        ],
                    },
                ],
            }, fh)

        with self.assertRaises(ValueError):
            StsMaker().make(config_file, quiet=True)

    def test_dict_mode_filter_exclude_basic(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'filter',
                        'exclude': r'[\U00010000-\U0010FFFF]',
                        'src': [
                            'dict.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                㑮陣\t𫝈阵
                陣\t阵
                㑮\t𫝈
                噹\t当 𰁸
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        self.assertEqual(os.path.join(self.root, 'dict.list'), stsdict)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '陣': ['阵'],
            '噹': ['当'],
        }, dict(converter.table))

    def test_dict_mode_filter_exclude_bad_regex(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'filter',
                        'exclude': r'???',
                        'src': [
                            'dict.txt',
                        ],
                    },
                ],
            }, fh)

        with self.assertRaises(ValueError):
            StsMaker().make(config_file, quiet=True)

    def test_dict_mode_filter_include_and_exclude(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'filter',
                        'include': r'^[\u0000-\uFFFF]*$',
                        'exclude': r'当',
                        'src': [
                            'dict.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                㑮陣\t𫝈阵
                陣\t阵
                㑮\t𫝈
                噹\t当 𰁸
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        self.assertEqual(os.path.join(self.root, 'dict.list'), stsdict)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '陣': ['阵'],
        }, dict(converter.table))

    def test_dict_mode_filter_method_remove_keys(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'filter',
                        'method': 'remove_keys',
                        'src': [
                            'dict.txt',
                            'exclude.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干\t幹 乾 干 榦 𠏉
                于\t於 于
                简\t簡
                单\t單
                """
            ))

        with open(os.path.join(self.root, 'exclude.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干\t幹 乾
                于\t
                单
                门\t門
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '简': ['簡'],
        }, dict(converter.table))

    def test_dict_mode_filter_method_remove_key_values(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'filter',
                        'method': 'remove_key_values',
                        'src': [
                            'dict.txt',
                            'exclude.txt',
                        ],
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干\t幹 乾 干 榦 𠏉
                于\t於 于
                简\t簡
                单\t單
                """
            ))

        with open(os.path.join(self.root, 'exclude.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干\t榦 𠏉 桿
                于
                单\t單
                门\t門
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual({
            '干': ['幹', '乾', '干'],
            '于': ['於'],
            '简': ['簡'],
        }, dict(converter.table))

    def test_dict_mode_filter_method_unknown(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'filter',
                        'method': 'unknown',
                        'src': [
                            'dict.txt',
                            'exclude.txt',
                        ],
                    },
                ],
            }, fh)

        with self.assertRaises(ValueError):
            StsMaker().make(config_file, quiet=True)

    def test_dict_sort(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'load',
                        'src': [
                            'phrases.txt',
                            'chars.txt',
                        ],
                        'sort': True,
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'phrases.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                干姜\t乾薑
                """
            ))

        with open(os.path.join(self.root, 'chars.txt'), 'w', encoding='UTF-8') as fh:
            fh.write(dedent(
                """\
                姜\t薑
                干\t幹 乾 干
                """
            ))

        stsdict = StsMaker().make(config_file, quiet=True)
        self.assertEqual(os.path.join(self.root, 'dict.list'), stsdict)
        with open(stsdict, encoding='UTF-8') as fh:
            self.assertEqual(
                '姜\t薑\n干\t幹 乾 干\n干姜\t乾薑\n',
                fh.read()
            )

    def test_dict_check(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.list',
                        'mode': 'load',
                        'src': [
                            'chars.txt',
                        ],
                        'check': True,
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'chars.txt'), 'w', encoding='UTF-8') as fh:
            fh.write('干\t幹 乾 干')

        with mock.patch('sts.StsDict.dump') as mocker:
            StsMaker().make(config_file, quiet=True)
            mocker.assert_called_with(mock.ANY, sort=mock.ANY, check=True)

    def test_get_config_file(self):
        # absolute path
        self.assertEqual(
            os.path.join(self.root, 'myconf.json'),
            StsMaker().get_config_file(os.path.join(self.root, 'myconf.json')),
        )

        # relative to CWD
        self.assertEqual(
            'myconf.json',
            StsMaker().get_config_file('myconf.json'),
        )
        self.assertEqual(
            os.path.normpath('subdir/myconf.json'),
            StsMaker().get_config_file('subdir/myconf.json'),
        )

        # relative to base_dir
        self.assertEqual(
            os.path.join(self.root, 'myconf.json'),
            StsMaker().get_config_file('myconf.json', base_dir=self.root),
        )
        self.assertEqual(
            os.path.normpath(os.path.join(self.root, 'subdir/myconf.json')),
            StsMaker().get_config_file('subdir/myconf.json', base_dir=self.root),
        )

        # relative to default config directory
        tmpfile = os.path.join(StsMaker.config_dir, '__dummy__.tmp.json')
        with open(tmpfile, 'w'):
            pass
        try:
            self.assertEqual(
                os.path.join(StsMaker.config_dir, '__dummy__.tmp.json'),
                StsMaker().get_config_file('__dummy__.tmp.json'),
            )
        finally:
            os.remove(tmpfile)

        # relative to default config directory (omit extension)
        for ext in ('json', 'yaml', 'yml'):
            with self.subTest(ext=ext):
                tmpfile = os.path.join(StsMaker.config_dir, f'__dummy__.tmp.{ext}')
                with open(tmpfile, 'w'):
                    pass
                try:
                    self.assertEqual(
                        os.path.join(StsMaker.config_dir, f'__dummy__.tmp.{ext}'),
                        StsMaker().get_config_file('__dummy__.tmp'),
                    )
                finally:
                    os.remove(tmpfile)

    def test_get_stsdict_file(self):
        # absolute path
        self.assertEqual(
            os.path.join(self.root, 'dict.list'),
            StsMaker().get_stsdict_file(os.path.join(self.root, 'dict.list')),
        )

        # relative to CWD
        self.assertEqual(
            'dict.list',
            StsMaker().get_stsdict_file('dict.list'),
        )
        self.assertEqual(
            os.path.normpath('subdir/dict.list'),
            StsMaker().get_stsdict_file('subdir/dict.list'),
        )

        # relative to base_dir
        self.assertEqual(
            os.path.join(self.root, 'dict.list'),
            StsMaker().get_stsdict_file('dict.list', base_dir=self.root),
        )
        self.assertEqual(
            os.path.normpath(os.path.join(self.root, 'subdir/dict.list')),
            StsMaker().get_stsdict_file('subdir/dict.list', base_dir=self.root),
        )

        # relative to default dictionary directory
        tmpfile = os.path.join(StsMaker.dictionary_dir, '__dummy__.tmp.txt')
        with open(tmpfile, 'w'):
            pass
        try:
            self.assertEqual(
                os.path.join(StsMaker.dictionary_dir, '__dummy__.tmp.txt'),
                StsMaker().get_stsdict_file('__dummy__.tmp.txt'),
            )
        finally:
            os.remove(tmpfile)

    def test_check_update_dict_scheme_file_src(self):
        # missing file
        file = os.path.join(self.root, 'conf.json')

        src1 = os.path.join(self.root, 'phrases.txt')
        with open(src1, 'w'):
            pass
        os.utime(src1, (20000, 20000))

        src2 = os.path.join(self.root, 'chars.txt')
        with open(src2, 'w'):
            pass
        os.utime(src2, (30000, 30000))

        scheme = {
            'file': file,
            'src': [src1, src2],
        }

        self.assertTrue(StsMaker().check_update(scheme))
        self.assertTrue(scheme['_updated'])

        # mtime(file) > mtime(src)
        file = os.path.join(self.root, 'conf.json')
        with open(file, 'w'):
            pass
        os.utime(file, (40000, 40000))

        src1 = os.path.join(self.root, 'phrases.txt')
        with open(src1, 'w'):
            pass
        os.utime(src1, (20000, 20000))

        src2 = os.path.join(self.root, 'chars.txt')
        with open(src2, 'w'):
            pass
        os.utime(src2, (30000, 30000))

        scheme = {
            'file': file,
            'src': [src1, src2],
        }

        self.assertFalse(StsMaker().check_update(scheme))
        self.assertNotIn('_updated', scheme)

        # mtime(file) < mtime(src)
        file = os.path.join(self.root, 'conf.json')
        with open(file, 'w'):
            pass
        os.utime(file, (10000, 10000))

        src1 = os.path.join(self.root, 'phrases.txt')
        with open(src1, 'w'):
            pass
        os.utime(src1, (20000, 20000))

        src2 = os.path.join(self.root, 'chars.txt')
        with open(src2, 'w'):
            pass
        os.utime(src2, (30000, 30000))

        scheme = {
            'file': file,
            'src': [src1, src2],
        }

        self.assertTrue(StsMaker().check_update(scheme))
        self.assertTrue(scheme['_updated'])

        # nested src update
        file = os.path.join(self.root, 'conf.json')
        with open(file, 'w'):
            pass
        os.utime(file, (40000, 40000))

        file1 = os.path.join(self.root, 'conf1.json')
        with open(file1, 'w'):
            pass
        os.utime(file1, (10000, 10000))

        src1 = os.path.join(self.root, 'phrases.txt')
        with open(src1, 'w'):
            pass
        os.utime(src1, (20000, 20000))

        scheme = {
            'file': file,
            'src': [
                {
                    'file': file1,
                    'mode': 'load',
                    'src': [src1],
                }
            ],
        }

        self.assertTrue(StsMaker().check_update(scheme))
        self.assertTrue(scheme['_updated'])

    def test_check_update_dict_scheme_file(self):
        # mtime(file) and unspecified mtime
        file = os.path.join(self.root, 'conf.json')
        with open(file, 'w'):
            pass
        os.utime(file, (20000, 20000))

        scheme = {
            'file': file,
        }

        self.assertFalse(StsMaker().check_update(scheme))
        self.assertNotIn('_updated', scheme)

        # mtime(file) > mtime
        file = os.path.join(self.root, 'conf.json')
        with open(file, 'w'):
            pass
        os.utime(file, (20000, 20000))

        scheme = {
            'file': file,
        }

        self.assertTrue(StsMaker().check_update(scheme, 10000))
        self.assertNotIn('_updated', scheme)

        # mtime(file) < mtime
        file = os.path.join(self.root, 'conf.json')
        with open(file, 'w'):
            pass
        os.utime(file, (20000, 20000))

        scheme = {
            'file': file,
        }

        self.assertFalse(StsMaker().check_update(scheme, 30000))
        self.assertNotIn('_updated', scheme)

    def test_check_update_dict_scheme_src(self):
        # mtime(src) and unspecified mtime
        src1 = os.path.join(self.root, 'phrases.txt')
        with open(src1, 'w'):
            pass
        os.utime(src1, (20000, 20000))

        src2 = os.path.join(self.root, 'chars.txt')
        with open(src2, 'w'):
            pass
        os.utime(src2, (30000, 30000))

        scheme = {
            'src': [src1, src2],
        }

        self.assertFalse(StsMaker().check_update(scheme))
        self.assertNotIn('_updated', scheme)

        # mtime(src) > mtime
        src1 = os.path.join(self.root, 'phrases.txt')
        with open(src1, 'w'):
            pass
        os.utime(src1, (20000, 20000))

        src2 = os.path.join(self.root, 'chars.txt')
        with open(src2, 'w'):
            pass
        os.utime(src2, (30000, 30000))

        scheme = {
            'src': [src1, src2],
        }

        self.assertTrue(StsMaker().check_update(scheme, 25000))
        self.assertTrue(scheme['_updated'])

        # mtime(src) < mtime
        src1 = os.path.join(self.root, 'phrases.txt')
        with open(src1, 'w'):
            pass
        os.utime(src1, (20000, 20000))

        src2 = os.path.join(self.root, 'chars.txt')
        with open(src2, 'w'):
            pass
        os.utime(src2, (30000, 30000))

        scheme = {
            'src': [src1, src2],
        }

        self.assertFalse(StsMaker().check_update(scheme, 40000))
        self.assertNotIn('_updated', scheme)

    def test_check_update_str(self):
        file = os.path.join(self.root, 'conf.json')
        with open(file, 'w'):
            pass
        os.utime(file, (20000, 20000))

        scheme = file

        self.assertFalse(StsMaker().check_update(scheme))
        self.assertFalse(StsMaker().check_update(scheme, mtime=30000))
        self.assertTrue(StsMaker().check_update(scheme, mtime=10000))


class TestStsConverter(unittest.TestCase):
    sample_s2t_dict = Trie({
        '干': ['幹', '乾', '干'],
        '了': ['了', '瞭'],
        '干了': ['幹了', '乾了'],
        '干涉': ['干涉'],
        '干柴': ['乾柴'],
        '虫': ['蟲'],
        '风': ['風'],
        '简': ['簡'],
        '转': ['轉'],
        '尸': ['屍', '尸'],
        '卜': ['卜', '蔔'],
        '发': ['發', '髮'],
        '财': ['財'],
        '发财': ['發財'],
        '圆': ['圓'],
        '梦': ['夢'],
    })

    sample_s2twp_dict = Trie({
        '驰': ['馳'],
        '奔馳': ['賓士'],
    })

    def setUp(self):
        """Set up a sub temp directory for testing."""
        self.root = tempfile.mkdtemp(dir=tmpdir)

    def test_init(self):
        # file as str (.list)
        tempfile = os.path.join(self.root, 'test.list')
        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""干\t幹 乾 干\n干姜\t乾薑""")
        converter = StsConverter(tempfile)
        self.assertEqual({'干': ['幹', '乾', '干'], '干姜': ['乾薑']}, converter.table)
        self.assertIs(Table, type(converter.table))

        # file as str (.jlist)
        tempfile = os.path.join(self.root, 'test.jlist')
        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""{"干": ["干", "榦"], "姜": ["姜", "薑"], "干姜": ["乾薑"]}""")
        converter = StsConverter(tempfile)
        self.assertEqual({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, converter.table)
        self.assertIs(Table, type(converter.table))

        # file as str (.tlist)
        tempfile = os.path.join(self.root, 'test.tlist')
        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""{"干": {"": ["干", "榦"], "姜": {"": ["乾薑"]}}, "姜": {"": ["姜", "薑"]}}""")
        converter = StsConverter(tempfile)
        self.assertEqual({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, converter.table)
        self.assertIs(Trie, type(converter.table))

        # file as os.PathLike object
        tempfile = Path(os.path.join(self.root, 'test-path-like.list'))
        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""干\t幹 乾 干\n干姜\t乾薑""")
        converter = StsConverter(tempfile)
        self.assertEqual({'干': ['幹', '乾', '干'], '干姜': ['乾薑']}, converter.table)
        self.assertIs(Table, type(converter.table))

        # StsDict
        stsdict = Trie({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        converter = StsConverter(stsdict)
        self.assertEqual({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}, converter.table)
        self.assertIs(stsdict, converter.table)

    def test_convert(self):
        converter = StsConverter(self.sample_s2t_dict)
        input = """干了 干涉 ⿱艹⿰虫风不需要简转繁"""
        expected = [(['干', '了'], ['幹了', '乾了']), ' ', (['干', '涉'], ['干涉']), ' ',
                    '⿱艹⿰虫风', '不', '需', '要', (['简'], ['簡']), (['转'], ['轉']), '繁']
        output = list(converter.convert(input))
        self.assertEqual(expected, output)

    def test_convert_exclude(self):
        converter = StsConverter(self.sample_s2t_dict)
        input = """-{尸}-廿山女田卜"""
        expected = [('尸',), '廿', '山', '女', '田', (['卜'], ['卜', '蔔'])]
        output = list(converter.convert(input, re.compile(r'-{(?P<return>.*?)}-')))
        self.assertEqual(expected, output)

        converter = StsConverter(self.sample_s2t_dict)
        input = """发财了<!-->财<--><!-->干<-->"""
        expected = [(['发', '财'], ['發財']), (['了'], ['了', '瞭']), ('财',), ('干',)]
        output = list(converter.convert(input, re.compile(r'<!-->(?P<return>.*?)<-->')))
        self.assertEqual(expected, output)

        converter = StsConverter(self.sample_s2twp_dict)
        input = """「奔馳」不是奔馳"""
        expected = [('「奔馳」',), '不', '是', (['奔', '馳'], ['賓士'])]
        output = list(converter.convert(input, re.compile(r'「.*?」')))
        self.assertEqual(expected, output)

        converter = StsConverter(self.sample_s2twp_dict)
        input = """奔-{}-驰"""  # noqa: P103
        expected = ['奔', (['驰'], ['馳'])]
        output = list(converter.convert(input, re.compile(r'-{(?P<return>.*?)}-')))  # noqa: P103
        self.assertEqual(expected, output)

        converter = StsConverter(self.sample_s2t_dict)
        input = """-{尸}-大口「发财了」"""
        expected = [('尸',), '大', '口', ('「发财了」',)]
        output = list(converter.convert(input, re.compile(r'「.*?」|-{(?P<return>.*?)}-')))
        self.assertEqual(expected, output)

        converter = StsConverter(self.sample_s2t_dict)
        input = """-{尸}-大口 <!-->财干<-->"""
        expected = [('尸',), '大', '口', ' ', ('财干',)]
        output = list(converter.convert(input, re.compile(r'-{(?P<return>.*?)}-|<!-->(?P<return2>.*?)<-->')))
        self.assertEqual(expected, output)

        converter = StsConverter(self.sample_s2twp_dict)
        input = """「奔馳」不是奔馳"""
        expected = [('「奔馳」',), '不', '是', (['奔', '馳'], ['賓士'])]
        output = list(converter.convert(input, re.compile(r'「(?P<nomatter>.*?)」')))
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
        input = dedent(
            """\
            干了 干涉
            ⿰虫风需要简转繁
            ⿱艹⿰虫风不需要简转繁
            沙⿰虫风也简转繁
            """
        )

        # txt
        expected = dedent(
            """\
            幹了 干涉
            𧍯需要簡轉繁
            ⿱艹⿰虫风不需要簡轉繁
            沙虱也簡轉繁
            """
        )
        output = ''.join(converter.convert_formatted(input, 'txt'))
        self.assertEqual(expected, output)

        # txtm
        expected = dedent(
            """\
            {{干->幹|乾|干}}了 {{干涉}}
            {{⿰虫风->𧍯}}需要{{简->簡}}{{转->轉}}繁
            ⿱艹⿰虫风不需要{{简->簡}}{{转->轉}}繁
            {{沙⿰虫风->沙虱}}也{{简->簡}}{{转->轉}}繁
            """
        )
        output = ''.join(converter.convert_formatted(input, 'txtm'))
        self.assertEqual(expected, output)

        # html
        expected = dedent(
            """\
            <a atomic><del hidden>干</del><ins>幹</ins><ins hidden>乾</ins><ins hidden>干</ins></a>了 <a><del hidden>干涉</del><ins>干涉</ins></a>
            <a atomic><del hidden>⿰虫风</del><ins>𧍯</ins></a>需要<a atomic><del hidden>简</del><ins>簡</ins></a><a atomic><del hidden>转</del><ins>轉</ins></a>繁
            ⿱艹⿰虫风不需要<a atomic><del hidden>简</del><ins>簡</ins></a><a atomic><del hidden>转</del><ins>轉</ins></a>繁
            <a><del hidden>沙⿰虫风</del><ins>沙虱</ins></a>也<a atomic><del hidden>简</del><ins>簡</ins></a><a atomic><del hidden>转</del><ins>轉</ins></a>繁
            """
        )
        output = ''.join(converter.convert_formatted(input, 'html'))
        self.assertEqual(expected, output)

        # json
        expected = (
            r"""[[["干"],["幹","乾","干"]],"了"," ",[["干","涉"],["干涉"]],"\n","""
            r"""[["⿰虫风"],["𧍯"]],"需","要",[["简"],["簡"]],[["转"],["轉"]],"繁","\n","""
            r""""⿱艹⿰虫风","不","需","要",[["简"],["簡"]],[["转"],["轉"]],"繁","\n","""
            r"""[["沙","⿰虫风"],["沙虱"]],"也",[["简"],["簡"]],[["转"],["轉"]],"繁","\n"]"""
        )
        output = ''.join(converter.convert_formatted(input, 'json'))
        self.assertEqual(expected, output)

    def test_convert_formatted_htmlpage(self):
        stsdict = Trie({
            '⿰虫风': ['𧍯'],
            '干': ['幹', '乾', '干'],
            '干涉': ['干涉'],
        })
        converter = StsConverter(stsdict)
        input = dedent(
            """\
            干了 干涉
            ⿰虫风 ⿱艹⿰虫风
            """
        )
        expected = dedent(
            """\
            <a atomic><del hidden>干</del><ins>幹</ins><ins hidden>乾</ins><ins hidden>干</ins></a>了 <a><del hidden>干涉</del><ins>干涉</ins></a>
            <a atomic><del hidden>⿰虫风</del><ins>𧍯</ins></a> ⿱艹⿰虫风
            """
        )

        # default template
        output = ''.join(converter.convert_formatted(input, 'htmlpage'))
        self.assertNotEqual(expected, output)
        self.assertIn(expected, output)

        # template placeholders
        converter.htmlpage_template = io.StringIO('%CONTENT%')
        output = ''.join(converter.convert_formatted(input, 'htmlpage'))
        self.assertEqual(expected, output)

        converter.htmlpage_template = io.StringIO('%VERSION%')
        output = ''.join(converter.convert_formatted(input, 'htmlpage'))
        self.assertEqual(sts_version, output)

        converter.htmlpage_template = io.StringIO('%%')
        output = ''.join(converter.convert_formatted(input, 'htmlpage'))
        self.assertEqual('%', output)

    def test_convert_formatted_exclude(self):
        stsdict = self.sample_s2t_dict
        converter = StsConverter(stsdict)
        exclude = re.compile(r'-{(?P<return>.*?)}-')
        input = '-{尸}-廿山女田卜'

        # txt
        expected = '尸廿山女田卜'
        output = ''.join(converter.convert_formatted(input, 'txt', exclude))
        self.assertEqual(expected, output)

        # txtm
        expected = '尸廿山女田{{卜->卜|蔔}}'
        output = ''.join(converter.convert_formatted(input, 'txtm', exclude))
        self.assertEqual(expected, output)

        # html
        expected = '尸廿山女田<a atomic><del hidden>卜</del><ins>卜</ins><ins hidden>蔔</ins></a>'
        output = ''.join(converter.convert_formatted(input, 'html', exclude))
        self.assertEqual(expected, output)

        # json
        expected = '[["尸"],"廿","山","女","田",[["卜"],["卜","蔔"]]]'
        output = ''.join(converter.convert_formatted(input, 'json', exclude))
        self.assertEqual(expected, output)

    def test_convert_text(self):
        converter = StsConverter(self.sample_s2t_dict)
        input = """干了 干涉 ⿱艹⿰虫风不需要简转繁"""
        expected = r"""幹了 干涉 ⿱艹⿰虫风不需要簡轉繁"""
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

        converter = StsConverter(self.sample_s2t_dict)

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

        converter = StsConverter(self.sample_s2t_dict)

        with mock.patch('sys.stdin', io.StringIO("""干柴烈火 发财圆梦""")):
            converter.convert_file(None, tempfile2)
        with open(tempfile2, 'r', encoding='UTF-8') as fh:
            result = fh.read()
        self.assertEqual("""乾柴烈火 發財圓夢""", result)

    def test_convert_file_stdout(self):
        tempfile = os.path.join(self.root, 'test.tmp')

        converter = StsConverter(self.sample_s2t_dict)

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


class TestStsConverterWithUnicode(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
