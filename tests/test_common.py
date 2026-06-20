import io
import json
import logging
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from functools import cached_property
from pathlib import Path
from textwrap import dedent
from unittest import mock

import yaml

from sts import __version__
from sts.common import (
    OcTable,
    RichTable,
    StreamList,
    StsConverter,
    StsDict,
    StsMaker,
    Table,
    Trie,
    Unicode,
)

root_dir = os.path.dirname(__file__)


def setUpModule():
    # Set up a temp directory for testing
    global _tmpdir, tmpdir
    _tmpdir = tempfile.TemporaryDirectory(prefix='init-')
    tmpdir = _tmpdir.name

    # suppress logging
    logging.disable(logging.CRITICAL)


def tearDownModule():
    # Cleanup the temp directory
    _tmpdir.cleanup()

    # unsuppress logging
    logging.disable(logging.NOTSET)


class TestStreamList(unittest.TestCase):
    def test_iterable(self):
        obj = []
        stream = StreamList(iter(obj))
        self.assertFalse(stream)
        self.assertEqual(list(stream), obj)
        self.assertEqual(list(stream), [])
        self.assertFalse(stream)

        obj = []
        stream = StreamList(iter(obj))
        self.assertEqual(list(stream), obj)
        self.assertEqual(list(stream), [])
        self.assertFalse(stream)

        obj = [1, 2, 3]
        stream = StreamList(iter(obj))
        self.assertTrue(stream)
        self.assertEqual(list(stream), obj)
        self.assertEqual(list(stream), [])
        self.assertTrue(stream)

        obj = [1, 2, 3]
        stream = StreamList(iter(obj))
        self.assertEqual(list(stream), obj)
        self.assertEqual(list(stream), [])
        self.assertTrue(stream)

        obj = [None]
        stream = StreamList(iter(obj))
        self.assertTrue(stream)
        self.assertEqual(list(stream), obj)
        self.assertEqual(list(stream), [])
        self.assertTrue(stream)

        obj = [None]
        stream = StreamList(iter(obj))
        self.assertEqual(list(stream), obj)
        self.assertEqual(list(stream), [])
        self.assertTrue(stream)

    def test_list(self):
        obj = []
        stream = StreamList(obj)
        self.assertFalse(stream)
        self.assertEqual(list(stream), obj)
        self.assertEqual(list(stream), [])
        self.assertFalse(stream)

        obj = []
        stream = StreamList(obj)
        self.assertEqual(list(stream), obj)
        self.assertEqual(list(stream), [])
        self.assertFalse(stream)

        obj = [1, 2, 3]
        stream = StreamList(obj)
        self.assertTrue(stream)
        self.assertEqual(list(stream), obj)
        self.assertEqual(list(stream), [])
        self.assertTrue(stream)

        obj = [1, 2, 3]
        stream = StreamList(obj)
        self.assertEqual(list(stream), obj)
        self.assertEqual(list(stream), [])
        self.assertTrue(stream)

        obj = [None]
        stream = StreamList(obj)
        self.assertTrue(stream)
        self.assertEqual(list(stream), obj)
        self.assertEqual(list(stream), [])
        self.assertTrue(stream)

        obj = [None]
        stream = StreamList(obj)
        self.assertEqual(list(stream), obj)
        self.assertEqual(list(stream), [])
        self.assertTrue(stream)


class TestUnicode(unittest.TestCase):
    def test_split_ids_basic(self):
        for ids in (
            '⿰木目', '⿱木口', '⿲彳氵亍', '⿳亠口小',
            '⿴囗口', '⿵𠘨皇', '⿷匚斤', '⿸疒丙',
            '⿹戈廾', '⿺走召', '⿻工从', '⿼叉丶',
            '⿽⺀十', '⿺走召', '⿻工从', '⿼叉丶', '⿽水丶',
            '⿾正', '⿿凹',
            '㇯豕一',
            '⿱艹⿰虫风', '⿱𡩧⿺進⿰貝招',
        ):
            with self.subTest(ids=ids):
                self.assertEqual(Unicode.split(ids), [ids])

        for coderange in (
            (0x20000, 0x2A6DF),  # Ext-B
            (0x2A700, 0x2B73F),  # Ext-C
            (0x2B740, 0x2B81F),  # Ext-D
            (0x2B820, 0x2CEAF),  # Ext-E
            (0x2CEB0, 0x2EBEF),  # Ext-F
            (0x30000, 0x3134F),  # Ext-G
            (0x31350, 0x323AF),  # Ext-H
            (0x2EBF0, 0x2EE5D),  # Ext-I
            (0xF900, 0xFAFF),    # CJK Compatibility Ideographs
            (0x2F800, 0x2FA1F),  # CJK Compatibility Ideographs Supplement
        ):
            with self.subTest(coderange=coderange):
                input = ''.join(('⿰', chr(coderange[0]), chr(coderange[1])))
                self.assertEqual(Unicode.split(input), [input])

    def test_split_ids_non_hanzi(self):
        self.assertEqual(Unicode.split('「⿰⿱⿲⿳」不影響'), ['「', '⿰⿱⿲⿳', '」', '不', '影', '響'])
        self.assertEqual(Unicode.split('⿰⿱⿲⿳ 不影響'), ['⿰⿱⿲⿳', ' ', '不', '影', '響'])
        self.assertEqual(Unicode.split('⿸⿹⿺⿻\n不影響'), ['⿸⿹⿺⿻', '\n', '不', '影', '響'])

    def test_split_ids_bad_length(self):
        self.assertEqual(Unicode.split('⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻長度不夠'), ['⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻長度不夠'])

    def test_split_vs(self):
        self.assertEqual(Unicode.split('刀劍󠄁 劍󠄃訢'), ['刀', '劍󠄁', ' ', '劍󠄃', '訢'])
        self.assertEqual(Unicode.split('刀劍󠄁󠄂 劍󠄁󠄂訢'), ['刀', '劍󠄁󠄂', ' ', '劍󠄁󠄂', '訢'])

    def test_split_ivi(self):
        self.assertEqual(Unicode.split('刀〾劍 〾劍訢 劍〾訢 〾劍〾訢'), ['刀', '〾劍', ' ', '〾劍', '訢', ' ', '劍', '〾訢', ' ', '〾劍', '〾訢'])
        self.assertEqual(Unicode.split('芀⿱〾艹劍󠄁無情'), ['芀', '⿱〾艹劍󠄁', '無', '情'])

    def test_split_other_composer(self):
        self.assertEqual(Unicode.split('A片 Å片 A̧片 Å̧片'), ['A', '片', ' ', 'Å', '片', ' ', 'A̧', '片', ' ', 'Å̧', '片'])
        self.assertEqual(Unicode.split('áéíóúý'), ['á', 'é', 'í', 'ó', 'ú', 'ý'])
        self.assertEqual(Unicode.split('áéíóúý'), ['á', 'é', 'í', 'ó', 'ú', 'ý'])
        self.assertNotEqual(Unicode.split('áéíóúý'), Unicode.split('áéíóúý'))
        self.assertEqual(
            Unicode.split('Lorem ipsum dolor sit amet.'),
            [
                'L', 'o', 'r', 'e', 'm', ' ',
                'i', 'p', 's', 'u', 'm', ' ',
                'd', 'o', 'l', 'o', 'r', ' ',
                's', 'i', 't', ' ',
                'a', 'm', 'e', 't', '.',
            ],
        )

    def test_is_hanzi(self):
        self.assertTrue(Unicode.is_hanzi(ord('⿰')))
        self.assertTrue(Unicode.is_hanzi(ord('　')))
        self.assertTrue(Unicode.is_hanzi(ord('〇')))
        self.assertTrue(Unicode.is_hanzi(ord('あ')))
        self.assertTrue(Unicode.is_hanzi(ord('ア')))
        self.assertTrue(Unicode.is_hanzi(ord('ㄅ')))
        self.assertTrue(Unicode.is_hanzi(ord('㆝')))
        self.assertTrue(Unicode.is_hanzi(ord('ㆠ')))
        self.assertTrue(Unicode.is_hanzi(ord('㋋')))
        self.assertTrue(Unicode.is_hanzi(ord('！')))
        self.assertTrue(Unicode.is_hanzi(ord('０')))
        self.assertTrue(Unicode.is_hanzi(ord('Ａ')))
        self.assertTrue(Unicode.is_hanzi(ord('ａ')))
        self.assertTrue(Unicode.is_hanzi(ord('～')))

        self.assertFalse(Unicode.is_hanzi(ord('.')))
        self.assertFalse(Unicode.is_hanzi(ord('?')))
        self.assertFalse(Unicode.is_hanzi(ord('·')))
        self.assertFalse(Unicode.is_hanzi(ord('0')))
        self.assertFalse(Unicode.is_hanzi(ord('9')))
        self.assertFalse(Unicode.is_hanzi(ord('A')))
        self.assertFalse(Unicode.is_hanzi(ord('Z')))
        self.assertFalse(Unicode.is_hanzi(ord('a')))
        self.assertFalse(Unicode.is_hanzi(ord('z')))
        self.assertFalse(Unicode.is_hanzi(ord('À')))


class TestStsDictBase(unittest.TestCase):
    @cached_property
    def root(self):
        """Lazily set up a sub temp directory for each test."""
        return tempfile.mkdtemp(dir=tmpdir)


class TestStsDict(TestStsDictBase):
    cls = StsDict

    def test_init(self):
        stsdict = self.cls({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

        stsdict = self.cls(StsDict({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}))
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

        stsdict = self.cls([('干', ['幹', '乾', '干']), ('姜', ['姜', '薑']), ('干姜', ['乾薑'])])
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

        stsdict = self.cls(干=['幹', '乾', '干'], 姜=['姜', '薑'], 干姜=['乾薑'])
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_repr(self):
        stsdict = self.cls({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertEqual(repr(stsdict), f'{stsdict.__class__.__name__}({dict(stsdict)})')
        self.assertEqual(eval(repr(stsdict)), stsdict)

    def test_getitem(self):
        stsdict = self.cls({'干': ['幹', '乾', '干'], '豆干': ['豆乾']})
        self.assertEqual(stsdict['干'], ['幹', '乾', '干'])
        self.assertEqual(stsdict['豆干'], ['豆乾'])
        with self.assertRaises(KeyError):
            stsdict['豆']
        with self.assertRaises(KeyError):
            stsdict['豆乾']

        # IDS/VS
        stsdict = self.cls({'⿰鱼土': ['𩵚'], '劒󠄁': ['劍󠄁']})
        self.assertEqual(stsdict['⿰鱼土'], ['𩵚'])
        self.assertEqual(stsdict['劒󠄁'], ['劍󠄁'])
        with self.assertRaises(KeyError):
            stsdict['劒']

    def test_contains(self):
        stsdict = self.cls({'干': ['幹', '乾', '干'], '豆干': ['豆乾']})
        self.assertIn('干', stsdict)
        self.assertIn('豆干', stsdict)
        self.assertNotIn('豆', stsdict)
        self.assertNotIn('豆乾', stsdict)

        # IDS/VS
        stsdict = self.cls({'⿰鱼土': ['𩵚'], '劒󠄁': ['劍󠄁']})
        self.assertIn('⿰鱼土', stsdict)
        self.assertIn('劒󠄁', stsdict)
        self.assertNotIn('劒', stsdict)

    def test_len(self):
        stsdict = self.cls()
        self.assertEqual(len(stsdict), 0)

        stsdict = self.cls({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertEqual(len(stsdict), 3)

    def test_iter(self):
        stsdict = self.cls({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertEqual(list(stsdict), ['干', '姜', '干姜'])

        # IDS/VS
        stsdict = self.cls({'⿰鱼土': ['𩵚'], '劒󠄁': ['劍󠄁']})
        self.assertEqual(list(stsdict), ['⿰鱼土', '劒󠄁'])

    def test_eq(self):
        dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
        stsdict = self.cls(dict_)
        self.assertTrue(stsdict == dict_)
        self.assertTrue(dict_ == stsdict)
        self.assertFalse(stsdict != dict_)
        self.assertFalse(dict_ != stsdict)

        dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
        dict2 = {'干姜': ['乾薑'], '干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
        stsdict = self.cls(dict_)
        self.assertTrue(stsdict == dict2)
        self.assertTrue(dict2 == stsdict)
        self.assertFalse(stsdict != dict2)
        self.assertFalse(dict2 != stsdict)

        dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
        dict2 = {'干姜': ['乾薑'], '干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
        stsdict = self.cls(dict_)
        stsdict2 = self.cls(dict2)
        self.assertTrue(stsdict == stsdict2)
        self.assertTrue(stsdict2 == stsdict)
        self.assertFalse(stsdict != stsdict2)
        self.assertFalse(stsdict2 != stsdict)

        dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
        dict2 = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
        stsdict = self.cls(dict_)
        self.assertFalse(stsdict == dict2)
        self.assertFalse(dict2 == stsdict)
        self.assertTrue(stsdict != dict2)
        self.assertTrue(dict2 != stsdict)

        dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
        dict2 = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
        stsdict = self.cls(dict_)
        self.assertFalse(stsdict == dict2)
        self.assertFalse(dict2 == stsdict)
        self.assertTrue(stsdict != dict2)
        self.assertTrue(dict2 != stsdict)

        dict_ = {'干': ['幹', '乾', '干', '𠏉'], '姜': ['姜', '薑']}
        dict2 = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑']}
        stsdict = self.cls(dict_)
        self.assertFalse(stsdict == dict2)
        self.assertFalse(dict2 == stsdict)
        self.assertTrue(stsdict != dict2)
        self.assertTrue(dict2 != stsdict)

    def test_delitem(self):
        stsdict = self.cls({'干姜': ['乾薑'], '姜': ['姜', '薑']})
        del stsdict['干姜']
        self.assertEqual(list(stsdict), ['姜'])

        stsdict = self.cls({'干姜': ['乾薑'], '姜': ['姜', '薑']})
        with self.assertRaises(KeyError):
            del stsdict['干']

        # IDS/VS
        stsdict = self.cls({'⿰鱼土': ['𩵚'], '劒󠄁': ['劍󠄁']})
        del stsdict['⿰鱼土']
        del stsdict['劒󠄁']
        self.assertEqual(list(stsdict), [])

    def test_keys(self):
        stsdict = self.cls({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertEqual(list(stsdict.keys()), ['干', '姜', '干姜'])

        # IDS/VS
        stsdict = self.cls({'⿰鱼土': ['𩵚'], '劒󠄁': ['劍󠄁']})
        self.assertEqual(list(stsdict.keys()), ['⿰鱼土', '劒󠄁'])

    def test_values(self):
        stsdict = self.cls({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertEqual([tuple(x) for x in stsdict.values()], [('幹', '乾', '干'), ('姜', '薑'), ('乾薑',)])

        # IDS/VS
        stsdict = self.cls({'⿰鱼土': ['𩵚'], '劒󠄁': ['劍󠄁']})
        self.assertEqual([tuple(x) for x in stsdict.values()], [('𩵚',), ('劍󠄁',)])

    def test_items(self):
        stsdict = self.cls({'干': ['幹', '乾'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertEqual(list(stsdict.items()), [('干', ['幹', '乾']), ('姜', ['姜', '薑']), ('干姜', ['乾薑'])])

        # IDS/VS
        stsdict = self.cls({'⿰鱼土': ['𩵚'], '劒󠄁': ['劍󠄁']})
        self.assertEqual(list(stsdict.items()), [('⿰鱼土', ['𩵚']), ('劒󠄁', ['劍󠄁'])])

    def test_add(self):
        # str
        stsdict = self.cls()

        stsdict.add('干', '幹')
        self.assertEqual(dict(stsdict), {'干': ['幹']})

        stsdict.add('干', '乾')
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾']})

        stsdict.add('姜', '姜')
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾'], '姜': ['姜']})

        # list
        stsdict = self.cls()

        stsdict.add('干', ['幹', '乾'])
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾']})

        stsdict.add('干', '干')
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾', '干']})

        stsdict.add('干', ['榦'])
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾', '干', '榦']})

        stsdict.add('姜', ['姜', '薑'])
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾', '干', '榦'], '姜': ['姜', '薑']})

        # iterable
        stsdict = self.cls()

        stsdict.add('干', ('幹', '乾'))
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾']})

        stsdict.add('干', iter(('幹', '乾', '干')))
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾', '干']})

    def test_add_skip_check(self):
        # list
        stsdict = self.cls({'干': ['幹', '乾']})

        stsdict.add('干', ['乾'])
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾']})

        stsdict.add('干', ['乾'], skip_check=True)
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾', '乾']})

        # iterable
        stsdict = self.cls()

        stsdict.add('干', ('幹', '乾'), skip_check=True)
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾']})

        stsdict.add('干', iter(('幹', '乾')), skip_check=True)
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾', '幹', '乾']})

    def test_update(self):
        stsdict = self.cls({'干': ['幹', '乾']})

        dict_ = StsDict({'干': ['干'], '姜': ['姜', '薑']})
        stsdict.update(dict_)
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾', '干'], '姜': ['姜', '薑']})

        dict_ = {'干': ['干', '榦'], '干姜': ['乾薑']}
        stsdict.update(dict_)
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾', '干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_load(self):
        # load as type when specified
        fi = io.StringIO()

        for type_ in (None, 'txt', 'tsv'):
            stsdict = self.cls()
            with mock.patch.object(stsdict, '_load_plain') as m_load:
                stsdict.load(fi, type=type_)
            m_load.assert_called_once_with(fi)

        for type_ in ('json', 'jlist'):
            stsdict = self.cls()
            with mock.patch.object(stsdict, '_load_json') as m_load:
                stsdict.load(fi, type=type_)
            m_load.assert_called_once_with(fi)

        for type_ in ('yaml', 'yml'):
            stsdict = self.cls()
            with mock.patch.object(stsdict, '_load_yaml') as m_load:
                stsdict.load(fi, type=type_)
            m_load.assert_called_once_with(fi)

        # determine type by extension if passed file is a str
        for ext in ('tmp', 'txt', 'tsv'):
            tempfile = os.path.join(self.root, f'test.{ext}')
            with open(tempfile, 'w', encoding='UTF-8'):
                pass
            stsdict = self.cls()
            with mock.patch.object(stsdict, '_load_plain') as m_load:
                stsdict.load(tempfile)
            m_load.assert_called_once_with(tempfile)

        for ext in ('json', 'jlist'):
            tempfile = os.path.join(self.root, f'test.{ext}')
            with open(tempfile, 'w', encoding='UTF-8'):
                pass
            stsdict = self.cls()
            with mock.patch.object(stsdict, '_load_json') as m_load:
                stsdict.load(tempfile)
            m_load.assert_called_once_with(tempfile)

        for ext in ('yaml', 'yml'):
            tempfile = os.path.join(self.root, f'test.{ext}')
            with open(tempfile, 'w', encoding='UTF-8'):
                pass
            stsdict = self.cls()
            with mock.patch.object(stsdict, '_load_yaml') as m_load:
                stsdict.load(tempfile)
            m_load.assert_called_once_with(tempfile)

        # determine type by extension if passed file is a path-like object
        tempfile = Path(os.path.join(self.root, 'test.yaml'))
        with open(tempfile, 'w', encoding='UTF-8'):
            pass
        stsdict = self.cls()
        with mock.patch.object(stsdict, '_load_yaml') as m_load:
            stsdict.load(tempfile)
        m_load.assert_called_once_with(tempfile)

    def test_load_plain(self):
        # basic
        stsdict = self.cls()
        stsdict.load(io.StringIO("""干\t幹 乾\n姜\t姜 薑"""))
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾'], '姜': ['姜', '薑']})

        # multiple loads
        stsdict = self.cls()
        stsdict.load(io.StringIO("""干\t幹 乾"""))
        stsdict.load(io.StringIO("""干\t干 榦\n姜\t姜 薑"""))
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾', '干', '榦'], '姜': ['姜', '薑']})

        # trailing linefeed
        stsdict = self.cls()
        stsdict.load(io.StringIO("""干\t幹\n"""))
        self.assertEqual(dict(stsdict), {'干': ['幹']})

        # empty value
        stsdict = self.cls()
        stsdict.load(io.StringIO("""干\t"""))
        self.assertEqual(dict(stsdict), {'干': ['']})

        # empty line (error in OpenCC < 1.1.4)
        stsdict = self.cls()
        stsdict.load(io.StringIO("""干\t幹\n\n于\t於"""))
        self.assertEqual(dict(stsdict), {'干': ['幹'], '于': ['於']})

        stsdict = self.cls()
        stsdict.load(io.StringIO("""干\t幹\n\n"""))
        self.assertEqual(dict(stsdict), {'干': ['幹']})

        # 0 tab: output same (error in OpenCC)
        stsdict = self.cls()
        stsdict.load(io.StringIO("""干\n于"""))
        self.assertEqual(dict(stsdict), {'干': ['干'], '于': ['于']})

        # 2 tabs: safely ignored (2nd tab treated as part of value in OpenCC)
        stsdict = self.cls()
        stsdict.load(io.StringIO("""干\t幹 乾\t# 一些註解"""))
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾']})

        # comment line
        stsdict = self.cls()
        stsdict.load(io.StringIO("""干\t幹 乾\n# 註解\n姜\t姜 薑"""))
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾'], '姜': ['姜', '薑']})

        stsdict = self.cls()
        stsdict.load(io.StringIO("""# 註解\n干\t幹 乾\n"""))
        self.assertEqual(dict(stsdict), {'干': ['幹', '乾']})

        # escaping
        stsdict = self.cls()
        stsdict.load(io.StringIO("""\\x00\\x09\\x0A\\x0D\\x20\\x23\\x7F\t\\x00\\x09\\x0A\\x0D\\x20\\x23\\x7F\n"""))
        self.assertEqual(dict(stsdict), {'\x00\t\n\r #\x7F': ['\x00\t\n\r #\x7F']})

        # invalid escaping
        stsdict = self.cls()
        stsdict.load(io.StringIO("""\\ \\\\ \\x \\xA \\x80 \\xFF\t字\n"""))
        self.assertEqual(dict(stsdict), {'\\ \\\\ \\x \\xA \\x80 \\xFF': ['字']})

    def test_load_json(self):
        # object as {key1: [value11, value12, ...], key2: [value21, value22, ...], ...}
        fi = io.StringIO()
        json.dump({'干': ['干', '幹', '乾'], '姜': ['姜', '薑']}, fi)
        fi.seek(0)
        stsdict = self.cls().load(fi, type='json')
        self.assertEqual(dict(stsdict), {'干': ['干', '幹', '乾'], '姜': ['姜', '薑']})

        # object as {key1: value1, key2: value2, ...}
        fi = io.StringIO()
        json.dump({'简': '簡', '单': '單'}, fi)
        fi.seek(0)
        stsdict = self.cls().load(fi, type='json')
        self.assertEqual(dict(stsdict), {'简': ['簡'], '单': ['單']})

        # array as [[key1, [value11, value12]], [key2, [value21, value22]], ...]
        fi = io.StringIO()
        json.dump([['干', ['干', '幹', '乾']], ['姜', ['姜', '薑']]], fi)
        fi.seek(0)
        stsdict = self.cls().load(fi, type='json')
        self.assertEqual(dict(stsdict), {'干': ['干', '幹', '乾'], '姜': ['姜', '薑']})

        # array as [[key1, value1], [key2, value2], ...]
        fi = io.StringIO()
        json.dump([['简', '簡'], ['单', '單']], fi)
        fi.seek(0)
        stsdict = self.cls().load(fi, type='json')
        self.assertEqual(dict(stsdict), {'简': ['簡'], '单': ['單']})

        # multiple loads
        f1 = io.StringIO()
        json.dump({'干': ['干', '幹', '乾']}, f1)
        f1.seek(0)
        f2 = io.StringIO()
        json.dump({'干': ['榦'], '姜': ['姜', '薑']}, f2)
        f2.seek(0)

        stsdict = self.cls()
        stsdict.load(f1, type='json')
        stsdict.load(f2, type='json')
        self.assertEqual(dict(stsdict), {'干': ['干', '幹', '乾', '榦'], '姜': ['姜', '薑']})

    def test_load_yaml(self):
        # object as {key1: [value11, value12, ...], key2: [value21, value22, ...], ...}
        fi = io.StringIO()
        yaml.dump({'干': ['干', '幹', '乾'], '姜': ['姜', '薑']}, fi)
        fi.seek(0)
        stsdict = self.cls().load(fi, type='yaml')
        self.assertEqual(dict(stsdict), {'干': ['干', '幹', '乾'], '姜': ['姜', '薑']})

        # object as {key1: value1, key2: value2, ...}
        fi = io.StringIO()
        yaml.dump({'简': '簡', '单': '單'}, fi)
        fi.seek(0)
        stsdict = self.cls().load(fi, type='yaml')
        self.assertEqual(dict(stsdict), {'简': ['簡'], '单': ['單']})

        # array as [[key1, [value11, value12]], [key2, [value21, value22]], ...]
        fi = io.StringIO()
        yaml.dump([['干', ['干', '幹', '乾']], ['姜', ['姜', '薑']]], fi)
        fi.seek(0)
        stsdict = self.cls().load(fi, type='yaml')
        self.assertEqual(dict(stsdict), {'干': ['干', '幹', '乾'], '姜': ['姜', '薑']})

        # array as [[key1, value1], [key2, value2], ...]
        fi = io.StringIO()
        yaml.dump([['简', '簡'], ['单', '單']], fi)
        fi.seek(0)
        stsdict = self.cls().load(fi, type='yaml')
        self.assertEqual(dict(stsdict), {'简': ['簡'], '单': ['單']})

        # multiple loads
        f1 = io.StringIO()
        yaml.dump({'干': ['干', '幹', '乾']}, f1)
        f1.seek(0)
        f2 = io.StringIO()
        yaml.dump({'干': ['榦'], '姜': ['姜', '薑']}, f2)
        f2.seek(0)

        stsdict = self.cls()
        stsdict.load(f1, type='yaml')
        stsdict.load(f2, type='yaml')
        self.assertEqual(dict(stsdict), {'干': ['干', '幹', '乾', '榦'], '姜': ['姜', '薑']})

    def test_dump(self):
        fo = io.StringIO()
        stsdict = self.cls({'干': ['干', '榦'], '姜': ['姜', '薑']})

        # no sort
        fo.seek(0)
        stsdict.dump(fo)
        text = fo.getvalue()
        self.assertEqual(text, '干\t干 榦\n姜\t姜 薑\n')

        # sort=False
        fo.seek(0)
        stsdict.dump(fo, sort=False)
        text = fo.getvalue()
        self.assertEqual(text, '干\t干 榦\n姜\t姜 薑\n')

        # sort=True
        fo.seek(0)
        stsdict.dump(fo, sort=True)
        text = fo.getvalue()
        self.assertEqual(text, '姜\t姜 薑\n干\t干 榦\n')

    def test_dump_file(self):
        tempfile = os.path.join(self.root, 'test.tmp')
        stsdict = self.cls({'干': ['干', '榦'], '姜': ['姜', '薑']})

        stsdict.dump(tempfile)
        with open(tempfile, 'r', encoding='UTF-8') as fh:
            text = fh.read()
        self.assertEqual(text, '干\t干 榦\n姜\t姜 薑\n')

        stsdict.dump(tempfile, sort=True)
        with open(tempfile, 'r', encoding='UTF-8') as fh:
            text = fh.read()
        self.assertEqual(text, '姜\t姜 薑\n干\t干 榦\n')

    def test_dump_stdout(self):
        stsdict = self.cls({'干': ['干', '榦'], '姜': ['姜', '薑']})
        with redirect_stdout(io.StringIO()) as fh:
            stsdict.dump()
        self.assertEqual(fh.getvalue(), '干\t干 榦\n姜\t姜 薑\n')

    def test_dump_empty_entry(self):
        stsdict = self.cls({'干': []})
        fo = io.StringIO()
        stsdict.dump(fo)
        text = fo.getvalue()
        self.assertEqual(text, '')

    def test_dump_badchar(self):
        stsdict = self.cls({'# \t\n\r': ['# \t\n\r']})
        fo = io.StringIO()
        stsdict.dump(fo)
        text = fo.getvalue()
        self.assertEqual(text, '\\x23 \\x09\\x0A\\x0D\t#\\x20\\x09\\x0A\\x0D\n')

        stsdict = self.cls({'\\x5C\\': ['\\x20\\']})
        fo = io.StringIO()
        stsdict.dump(fo)
        text = fo.getvalue()
        self.assertEqual(text, '\\x5Cx5C\\\t\\x5Cx20\\\n')

    def test_loadjson(self):
        fi = io.StringIO('{"干": ["干", "榦"], "姜": ["姜", "薑"], "干姜": ["乾薑"]}')
        stsdict = self.cls().loadjson(fi)
        self.assertEqual(dict(stsdict), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_loadjson_file(self):
        tempfile = os.path.join(self.root, 'test.tmp')

        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write('{"干": ["干", "榦"], "姜": ["姜", "薑"], "干姜": ["乾薑"]}')
        stsdict = self.cls().loadjson(tempfile)
        self.assertEqual(dict(stsdict), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_dumpjson(self):
        stsdict = self.cls({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        fo = io.StringIO()
        stsdict.dumpjson(fo)
        fo.seek(0)
        self.assertEqual(json.load(fo), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_dumpjson_file(self):
        tempfile = os.path.join(self.root, 'test.tmp')

        stsdict = self.cls({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        stsdict.dumpjson(tempfile)
        with open(tempfile, 'r', encoding='UTF-8') as fh:
            self.assertEqual(json.load(fh), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_dumpjson_stdout(self):
        stsdict = self.cls({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        with redirect_stdout(io.StringIO()) as fh:
            stsdict.dumpjson()
        self.assertEqual(json.loads(fh.getvalue()), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_match(self):
        stsdict = self.cls({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
        self.assertIsNone(stsdict.match('吃干姜了', 0))
        self.assertEqual(stsdict.match('吃干姜了', 1), ((['干', '姜'], ['乾薑']), 1, 3))
        self.assertEqual(stsdict.match('吃干姜了', 2), ((['姜'], ['姜', '薑']), 2, 3))
        self.assertIsNone(stsdict.match('吃干姜了', 3))

        # an empty stsdict never match
        stsdict = self.cls()
        self.assertIsNone(stsdict.match('需要', 0))

        # treat empty values as no match
        stsdict = self.cls({'需': []})
        self.assertIsNone(stsdict.match('需要', 0))

        stsdict = self.cls({'需': ['須'], '需要': []})
        self.assertEqual(stsdict.match('需要', 0), ((['需'], ['須']), 0, 1))

    def test_apply(self):
        stsdict = self.cls({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
        self.assertEqual(list(stsdict.apply('吃干姜了')), ['吃', (['干', '姜'], ['乾薑']), '了'])

    def test_apply_enum(self):
        stsdict = self.cls({'钟': ['鐘', '鍾'], '药': ['藥', '葯'], '用药': ['用藥']})
        self.assertEqual(
            stsdict.apply_enum('看钟用药', include_short=False, include_self=False),
            ['看鐘用藥', '看鍾用藥'],
        )
        self.assertEqual(
            stsdict.apply_enum('看钟用药', include_short=True, include_self=False),
            ['看鐘用藥', '看鐘用葯', '看鍾用藥', '看鍾用葯'],
        )
        self.assertEqual(
            stsdict.apply_enum('看钟用药', include_short=False, include_self=True),
            ['看鐘用藥', '看鐘用药', '看鍾用藥', '看鍾用药', '看钟用藥', '看钟用药'],
        )
        self.assertEqual(
            stsdict.apply_enum('看钟用药', include_short=True, include_self=True),
            ['看鐘用藥', '看鐘用药', '看鐘用葯', '看鍾用藥', '看鍾用药', '看鍾用葯', '看钟用藥', '看钟用药', '看钟用葯'],
        )

    def test_apply_enum2(self):
        stsdict = self.cls({'采信': ['採信'], '信息': ['訊息']})
        self.assertEqual(
            stsdict.apply_enum('采信息', include_short=False, include_self=False),
            ['採信息'],
        )
        self.assertEqual(
            stsdict.apply_enum('采信息', include_short=True, include_self=False),
            ['採信息', '采訊息'],
        )
        self.assertEqual(
            stsdict.apply_enum('采信息', include_short=False, include_self=True),
            ['採信息', '采信息'],
        )
        self.assertEqual(
            stsdict.apply_enum('采信息', include_short=True, include_self=True),
            ['採信息', '采信息', '采訊息'],
        )

    def test_join(self):
        # postfix: basic
        stsdict = self.cls({'因为': ['因爲']})
        stsdict2 = Table({'爲': ['為']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {'因为': ['因為'], '爲': ['為']})

        # postfix: multi values
        stsdict = self.cls({'干吗': ['幹嗎', '乾嗎']})
        stsdict2 = Table({'幹嗎': ['幹嘛', '幹嗎']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {'干吗': ['幹嘛', '幹嗎', '乾嗎'], '幹嗎': ['幹嘛', '幹嗎']})

        # prefix: a value same as another converted value
        # 说 => 説 => 說
        stsdict = self.cls({'说': ['說', '説']})
        stsdict2 = Table({'説': ['說']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {'说': ['說'], '説': ['說']})

        # prefix: major value
        # 納米 => (reversed) => 纳米 => (reconverted) => 納米:奈米
        stsdict = self.cls({'纳': ['納']})
        stsdict2 = Table({'納米': ['奈米']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {'纳': ['納'], '納米': ['奈米'], '纳米': ['奈米']})

        # prefix: minor value
        # 奶娘 => (reversed) => 妳娘 => (reconverted) => 你娘 奶娘:奶媽
        stsdict = self.cls({'妳': ['你', '奶']})
        stsdict2 = Table({'奶娘': ['奶媽']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {
            '妳': ['你', '奶'],
            '妳娘': ['你娘', '奶媽'],
            '奶娘': ['奶媽'],
        })

        # prefix: another reconverted value exists
        # 奶娘 => (reversed) => 妳娘 => (reconverted) => 你娘:妳媽 奶娘:奶媽
        stsdict = self.cls({'妳': ['你', '奶']})
        stsdict2 = Table({'奶娘': ['奶媽'], '你娘': ['妳媽']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {
            '妳': ['你', '奶'],
            '妳娘': ['妳媽', '奶媽'],
            '奶娘': ['奶媽'],
            '你娘': ['妳媽'],
        })

        # prefix: multi reversed values
        # 正則表達式 => (reversed) => 正则表达式 正则表達式 正則表达式 正則表達式 => (reconverted) => ...
        stsdict = self.cls({'则': ['則'], '表达': ['表達']})
        stsdict2 = Table({'正則表達式': ['正規表示式']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {
            '则': ['則'], '表达': ['表達'],
            '正则表达式': ['正規表示式'],
            '正则表達式': ['正規表示式'],
            '正則表达式': ['正規表示式'],
            '正則表達式': ['正規表示式'],
        })

        # prefix: multi reversed values with multi reconverted values
        # 奶娘 => (reversed) => 妳孃 妳娘 奶孃 => (reconverted) => ...
        stsdict = self.cls({'妳': ['你', '奶'], '孃': ['娘']})
        stsdict2 = Table({'奶娘': ['奶媽']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {
            '妳': ['你', '奶'], '孃': ['娘'],
            '妳孃': ['你娘', '奶媽'],
            '妳娘': ['你娘', '奶媽'],
            '奶孃': ['奶媽'],
            '奶娘': ['奶媽'],
        })

        stsdict = self.cls({'万用字元': ['萬用字元'], '数据': ['數據']})
        stsdict2 = Table({'數據': ['資料'], '元數據': ['後設資料']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {
            '万用字元': ['萬用字元'],
            '数据': ['資料'],
            '數據': ['資料'],
            '元数据': ['後設資料'],
            '元數據': ['後設資料'],
        })

        # prefix: multi reversed values with phrase
        # 彙編 => (reversed) => 汇编 彙編 汇編 彙编 => (reconverted) => ...
        stsdict = self.cls({'汇': ['匯', '彙'], '编': ['編'], '汇编': ['彙編']})
        stsdict2 = Table({'彙編': ['組譯']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {
            '汇': ['匯', '彙'], '编': ['編'], '汇编': ['組譯'],
            '彙編': ['組譯'], '汇編': ['匯編', '組譯'], '彙编': ['組譯'],
        })

        # prefix: multi keys reversed to same
        # 白干 白幹 白乾 => (reversed) => 白干 => (reconverted) => 白幹 白乾 白干 => ...
        stsdict = self.cls({'干': ['幹', '乾', '干']})
        stsdict2 = Table({'白干': ['白干酒'], '白幹': ['白做'], '白乾': ['白乾杯']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {
            '干': ['幹', '乾', '干'],
            '白干': ['白做', '白乾杯', '白干酒'],
            '白幹': ['白做'], '白乾': ['白乾杯'],
        })

        # prefix
        stsdict = self.cls({'数': ['數'], '据': ['據', '据'], '数据': ['資料']})
        stsdict2 = Table({'大資料': ['大量資料'], '大數據': ['大數據']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {
            '数': ['數'], '据': ['據', '据'], '数据': ['資料'],
            '大数据': ['大量資料'], '大資料': ['大量資料'],
            '大数據': ['大數據'], '大數据': ['大數據', '大數据'], '大數據': ['大數據'],
        })

        # prefix: prior dict needs complete phrases to prevent undesired cases
        # 品質量表 => (reversed) => 品质量表 => (reconverted) => 品質量表 品質量錶 => ...
        stsdict = self.cls({'质': ['質'], '表': ['表', '錶']})
        stsdict2 = Table({'質量': ['質量', '品質'], '品質量表': ['品質量表']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {
            '质': ['質'], '表': ['表', '錶'],
            '质量': ['質量', '品質'], '質量': ['質量', '品質'],
            '品质量表': ['品質量表', '品質量錶', '品品質錶'],
            '品質量表': ['品質量表', '品質量錶', '品品質錶'],
        })

        # 品質量表 => (reversed) => 品质量表 => (reconverted) => 品質量表 => ...
        stsdict = self.cls({'质': ['質'], '表': ['表', '錶'], '量表': ['量表']})
        stsdict2 = Table({'質量': ['質量', '品質'], '品質量表': ['品質量表']})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {
            '质': ['質'], '表': ['表', '錶'], '量表': ['量表'],
            '质量': ['質量', '品質'], '質量': ['質量', '品質'],
            '品质量表': ['品質量表'], '品質量表': ['品質量表'],
        })

        # remove entries with empty values
        stsdict = self.cls({'文': []})
        stsdict2 = Table({'字': []})
        stsdict = stsdict.join(stsdict2)
        self.assertEqual(dict(stsdict), {})


class TestTable(TestStsDict):
    cls = Table

    def test_loadjson(self):
        fi = io.StringIO('{"干": ["干", "榦"], "姜": ["姜", "薑"], "干姜": ["乾薑"]}')
        stsdict = self.cls().loadjson(fi)
        self.assertEqual(dict(stsdict), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_loadjson_file(self):
        tempfile = os.path.join(self.root, 'test.tmp')

        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write('{"干": ["干", "榦"], "姜": ["姜", "薑"], "干姜": ["乾薑"]}')
        stsdict = self.cls().loadjson(tempfile)
        self.assertEqual(dict(stsdict), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_dumpjson(self):
        stsdict = self.cls({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        fo = io.StringIO()
        stsdict.dumpjson(fo)
        fo.seek(0)
        self.assertEqual(json.load(fo), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_dumpjson_file(self):
        tempfile = os.path.join(self.root, 'test.tmp')

        stsdict = self.cls({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        stsdict.dumpjson(tempfile)
        with open(tempfile, 'r', encoding='UTF-8') as fh:
            self.assertEqual(json.load(fh), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_dumpjson_stdout(self):
        stsdict = self.cls({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        with redirect_stdout(io.StringIO()) as fh:
            stsdict.dumpjson()
        self.assertEqual(json.loads(fh.getvalue()), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_head_map_basic(self):
        # basic
        stsdict = Table({
            '干': ['幹', '乾'],
            '干姜': ['乾薑'],
            '干不下': ['幹不下'],
            '干不了': ['幹不了'],
            '姜': ['姜', '薑'],
        })
        self.assertEqual(stsdict.head_map, {'干姜': 2, '干不': 3})

        stsdict = Table({
            '干不干净': ['乾不乾淨'],
            '干': ['幹', '乾'],
            '干姜': ['乾薑'],
            '干不下': ['幹不下'],
            '干不了': ['幹不了'],
        })
        self.assertEqual(stsdict.head_map, {'干不': 4, '干姜': 2})

        # IDS
        stsdict = Table({'⿰虫风': ['𧍯'], '沙⿰虫风': ['沙虱']})
        self.assertEqual(stsdict.head_map, {'沙⿰虫风': 2})

    def test_head_map_cache(self):
        # getter
        stsdict = Table({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']})
        dict_ = stsdict.head_map
        self.assertEqual(dict_, {'干姜': 2})
        self.assertIs(dict_, stsdict.head_map)

        # should update automatically after changed
        stsdict.add('了', ['了', '瞭'])
        stsdict.add('不了解', ['不瞭解'])
        self.assertEqual(stsdict.head_map, {'干姜': 2, '不了': 3})

        stsdict.update({'我不了解': ['我不瞭解']})
        self.assertEqual(stsdict.head_map, {'干姜': 2, '不了': 3, '我不': 4})


class TestTrie(TestStsDict):
    cls = Trie

    def test_iter(self):
        # keys are re-ordered by prefix
        stsdict = self.cls({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertEqual(list(stsdict), ['干', '干姜', '姜'])

        # IDS/VS
        stsdict = self.cls({'⿰鱼土': ['𩵚'], '劒󠄁': ['劍󠄁']})
        self.assertEqual(list(stsdict), ['⿰鱼土', '劒󠄁'])

    def test_keys(self):
        # keys are re-ordered by prefix
        stsdict = self.cls({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertEqual(list(stsdict.keys()), ['干', '干姜', '姜'])

        # IDS/VS
        stsdict = self.cls({'⿰鱼土': ['𩵚'], '劒󠄁': ['劍󠄁']})
        self.assertEqual(list(stsdict.keys()), ['⿰鱼土', '劒󠄁'])

    def test_values(self):
        # keys are re-ordered by prefix
        stsdict = self.cls({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertEqual([tuple(x) for x in stsdict.values()], [('幹', '乾', '干'), ('乾薑',), ('姜', '薑')])

        # IDS/VS
        stsdict = self.cls({'⿰鱼土': ['𩵚'], '劒󠄁': ['劍󠄁']})
        self.assertEqual([tuple(x) for x in stsdict.values()], [('𩵚',), ('劍󠄁',)])

    def test_items(self):
        # keys are re-ordered by prefix
        stsdict = self.cls({'干': ['幹', '乾'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertEqual(list(stsdict.items()), [('干', ['幹', '乾']), ('干姜', ['乾薑']), ('姜', ['姜', '薑'])])

        # IDS/VS
        stsdict = self.cls({'⿰鱼土': ['𩵚'], '劒󠄁': ['劍󠄁']})
        self.assertEqual(list(stsdict.items()), [('⿰鱼土', ['𩵚']), ('劒󠄁', ['劍󠄁'])])

    def test_loadjson(self):
        fi = io.StringIO('{"干": {"": ["干", "榦"], "姜": {"": ["乾薑"]}}, "姜": {"": ["姜", "薑"]}}')
        stsdict = self.cls().loadjson(fi)
        self.assertEqual(dict(stsdict), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_loadjson_file(self):
        tempfile = os.path.join(self.root, 'test.tmp')

        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write('{"干": {"": ["干", "榦"], "姜": {"": ["乾薑"]}}, "姜": {"": ["姜", "薑"]}}')
        stsdict = self.cls().loadjson(tempfile)
        self.assertEqual(dict(stsdict), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_dumpjson(self):
        stsdict = self.cls({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        fo = io.StringIO()
        stsdict.dumpjson(fo)
        fo.seek(0)
        self.assertEqual(json.load(fo), {'干': {'': ['干', '榦'], '姜': {'': ['乾薑']}}, '姜': {'': ['姜', '薑']}})

        # IDS/VS: should be Unicode char based
        stsdict = self.cls({'⿰鱼土': ['𩵚'], '劒󠄁': ['劍󠄁']})
        fo = io.StringIO()
        stsdict.dumpjson(fo)
        fo.seek(0)
        self.assertEqual(json.load(fo), {'⿰': {'鱼': {'土': {'': ['𩵚']}}}, '劒': {'󠄁': {'': ['劍󠄁']}}})

    def test_dumpjson_file(self):
        tempfile = os.path.join(self.root, 'test.tmp')

        stsdict = self.cls({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        stsdict.dumpjson(tempfile)
        with open(tempfile, 'r', encoding='UTF-8') as fh:
            self.assertEqual(json.load(fh), {'干': {'': ['干', '榦'], '姜': {'': ['乾薑']}}, '姜': {'': ['姜', '薑']}})

    def test_dumpjson_stdout(self):
        stsdict = self.cls({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        with redirect_stdout(io.StringIO()) as fh:
            stsdict.dumpjson()
        self.assertEqual(json.loads(fh.getvalue()), {'干': {'': ['干', '榦'], '姜': {'': ['乾薑']}}, '姜': {'': ['姜', '薑']}})


class TestRichTable(TestStsDict):
    cls = RichTable

    def test_dup_key_merge_uncommented(self):
        table = self.cls().load(io.StringIO('a\tA1 A2\na\tA2 A3\n'))
        self.assertEqual(table, {'a': ['A1', 'A2', 'A3']})

        table = self.cls().load(io.StringIO('a\na\n'))
        self.assertEqual(table, {'a': ['a']})

    def test_dup_key_raise_on_commented(self):
        with self.assertRaisesRegex(ValueError, "Duplicated key 'a' at line 3"):
            self.cls().load(io.StringIO('a\tA1\n# comment\na\tA2\n'))

    def test_dup_key_raise_on_extra(self):
        with self.assertRaisesRegex(ValueError, "Duplicated key 'a' at line 2"):
            self.cls().load(io.StringIO('a\tA1\na\tA2\textra\n'))

    def _test_sort(self, input, expected):
        table = self.cls().load(io.StringIO(input))
        fo = io.StringIO()
        table.dump(fo, sort=True)
        text = fo.getvalue()
        self.assertEqual(text, expected)

    def test_sort_moves_comment_with_following_entry(self):
        self._test_sort(
            'b\tB\n# comment for a\na\tA\n',
            '# comment for a\na\tA\nb\tB\n',
        )

    def test_sort_preserves_blank_lines_in_anchored_block(self):
        self._test_sort(
            'b\tB\n\n# comment for a\na\tA\n',
            '\n# comment for a\na\tA\nb\tB\n',
        )

    def test_sort_splits_header_from_first_entry_comment(self):
        self._test_sort(
            '# Header\n\n# comment for b\nb\tB\na\tA\n',
            '# Header\n\na\tA\n# comment for b\nb\tB\n',
        )

    def test_sort_keeps_footer_at_end(self):
        self._test_sort(
            'b\tB\na\tA\n\n# footer\n',
            'a\tA\nb\tB\n\n# footer\n',
        )

    def test_sort_moves_extra_with_entry(self):
        self._test_sort(
            'b\tB\textra\tdata\na\tA\n',
            'a\tA\nb\tB\textra\tdata\n',
        )


class TestOcTable(TestStsDictBase):
    cls = OcTable

    def test_load_plain(self):
        # basic
        table = self.cls()
        table.load(io.StringIO("""干\t幹 乾\n姜\t姜 薑\n"""))
        self.assertEqual(table, {'干': ['幹', '乾'], '姜': ['姜', '薑']})

        # empty line: skip (error in OpenCC < 1.1.4)
        table = self.cls()
        table.load(io.StringIO("""干\t幹\n\n于\t於\n"""))
        self.assertEqual(table, {'干': ['幹'], '于': ['於']})

        # 0 tab: error
        table = self.cls()
        with self.assertRaises(ValueError):
            table.load(io.StringIO("""干"""))

        # 2 tabs: 2nd tab treated as part of value
        table = self.cls()
        table.load(io.StringIO("""干\t幹\t附註"""))
        self.assertEqual(table, {'干': ['幹\t附註']})

        # duplicated key: error
        table = self.cls()
        with self.assertRaises(ValueError):
            table.load(io.StringIO("""干\t幹\n干\t乾"""))

        # comment line
        table = self.cls()
        table.load(io.StringIO("""# 註解\n干\t幹 乾\n"""))
        self.assertEqual(table, {'干': ['幹', '乾']})

    def test_dump(self):
        # basic
        table = self.cls({'A': ['a1', 'a2'], 'B': ['b1', 'b2']})
        fo = io.StringIO()
        table.dump(fo)
        self.assertEqual(fo.getvalue(), 'A\ta1 a2\nB\tb1 b2\n')

        # allowed special chars
        table = self.cls({'A B': ['#A\tB']})
        fo = io.StringIO()
        table.dump(fo)
        self.assertEqual(fo.getvalue(), 'A B\t#A\tB\n')

        # leading '#' in key
        with self.assertRaises(ValueError):
            self.cls({'#': ['x']}).dump(io.StringIO())

        # badchar in key
        for badchar in ('\t', '\n', '\r'):
            with self.subTest(type='key', badchar=badchar):
                with self.assertRaises(ValueError):
                    self.cls({badchar: ['x']}).dump(io.StringIO())

        # badchar in value
        for badchar in (' ', '\n', '\r'):
            with self.subTest(type='value', badchar=badchar):
                with self.assertRaises(ValueError):
                    self.cls({'x': [badchar]}).dump(io.StringIO())


class TestStsMaker(unittest.TestCase):
    def setUp(self):
        """Set up a sub temp directory for testing."""
        self.root = tempfile.mkdtemp(dir=tmpdir)

    def test_load_config_json(self):
        """Should load a file with .json extension as JSON"""
        config_file = os.path.join(self.root, 'config.json')

        # should load a normal JSON
        expected = {'dicts': []}
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump(expected, fh)

        self.assertEqual(StsMaker().load_config(config_file), expected)

        # should raise for malformed JSON
        with open(config_file, 'w', encoding='UTF-8') as fh:
            fh.write('dicts: []')

        with self.assertRaises(json.decoder.JSONDecodeError):
            StsMaker().load_config(config_file)

    def test_load_config_yaml(self):
        """Should load a file with non-json extension as YAML"""
        for ext in ('', '.yaml', '.yml', '.custom'):
            with self.subTest(ext=ext):
                config_file = os.path.join(self.root, f'config{ext}')

                with open(config_file, 'w', encoding='UTF-8') as fh:
                    fh.write('dicts: []')

                self.assertEqual(StsMaker().load_config(config_file), {'dicts': []})

    def test_bad_config_object(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump([], fh)

        with self.assertRaises(RuntimeError):
            StsMaker().make(config_file)

    def test_no_dicts(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({}, fh)

        with self.assertRaises(RuntimeError):
            StsMaker().make(config_file)

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

        dest = StsMaker().make(config_file)
        self.assertEqual(dest, os.path.join(self.root, 'dict.txt'))

    def test_dict_str_missing_file(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    'dict.txt',
                ],
            }, fh)

        with self.assertRaises(RuntimeError):
            StsMaker().make(config_file)

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
            StsMaker().make(config_file)

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

        dest = StsMaker().make(config_file)
        self.assertEqual(dest, os.path.join(self.root, 'dict.txt'))

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
            StsMaker().make(config_file)

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '幹你娘': ['干你娘'],
            '幹': ['干'],
            '乾': ['干'],
            '干': ['干'],
        })

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

        dest = StsMaker().make(config_file)
        self.assertEqual(dest, os.path.join(self.root, 'dict.list'))
        with open(dest, encoding='UTF-8') as fh:
            self.assertEqual(
                fh.read(),
                '干姜\t乾薑\n姜\t薑\n干\t幹 乾 干\n',
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

        dest = StsMaker().make(config_file)
        self.assertEqual(dest, os.path.join(self.root, 'dict.jlist'))
        with open(dest, encoding='UTF-8') as fh:
            self.assertEqual(
                fh.read(),
                '{"干姜":["乾薑"],"姜":["薑"],"干":["幹","乾","干"]}',
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

        dest = StsMaker().make(config_file)
        self.assertEqual(dest, os.path.join(self.root, 'dict.tlist'))
        with open(dest, encoding='UTF-8') as fh:
            self.assertEqual(
                fh.read(),
                '{"干":{"姜":{"":["乾薑"]},"":["幹","乾","干"]},"姜":{"":["薑"]}}',
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

        dest = StsMaker().make(config_file)
        self.assertEqual(dest, os.path.join(self.root, 'dict.txt'))
        with open(dest, encoding='UTF-8') as fh:
            self.assertEqual(
                fh.read(),
                '干姜\t乾薑\n姜\t薑\n干\t幹 乾 干\n',
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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '干你娘': ['幹你娘'],
            '干姜': ['乾薑'],
            '干娘': ['乾娘'],
            '姜': ['薑'],
            '干': ['幹', '乾', '干'],
            '贵': ['貴'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '姜': ['薑'],
            '干': ['幹', '乾', '干'],
            '贵': ['貴'],
            '干你娘': ['幹你娘'],
            '干姜': ['乾薑'],
            '干娘': ['乾娘'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '幹你娘': ['干你娘'],
            '乾薑': ['干姜'],
            '乾娘': ['干娘'],
            '薑': ['姜'],
            '幹': ['干'],
            '乾': ['干'],
            '干': ['干'],
            '貴': ['贵'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '开': ['開'],
            '碱': ['鹼'],
            '胆': ['膽'],
            '驰': ['馳'],
            '锿': ['鑀'],
            '奔馳': ['賓士'],
            '酰': ['醯'],
            '鎄': ['鑀'],
            '奔驰': ['賓士'],
        })

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

        dest = StsMaker().make(config_file)
        self.assertEqual(dest, os.path.join(self.root, 'dict.list'))
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '表': ['表', '錶'],
            '规': ['規'],
            '则': ['則'],
            '达': ['達'],
            '运': ['運'],
            '表达': ['表達'],
            '表达式': ['表示式', '運算式'],
            '表達式': ['表示式', '運算式', '錶達式'],
            '正则表达式': ['正規表示式'],
            '正则表達式': ['正規表示式', '正則錶達式'],
            '正則表达式': ['正規表示式'],
            '正則表達式': ['正規表示式', '正則錶達式'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '表示式': ['表达式'],
            '運算式': ['表达式'],
            '正規表示式': ['正则表达式'],
            '規': ['规'],
            '則': ['则'],
            '達': ['达'],
            '運': ['运'],
            '表達': ['表达'],
            '表達式': ['表达式'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '采': ['採'],
            '采信': ['採信'],
            '信息': ['資訊'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '１里壹': ['１里壹'],
            '１里貳': ['１里贰'],
            '１里叄': ['１里叁'],
            '２里壹': ['２里壹'],
            '２里貳': ['２里贰'],
            '２里叄': ['２里叁'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '壹里': ['壹里'],
            '貳里': ['贰里'],
            '叄里': ['叁里'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '里': ['裏', '里'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '１里１': ['１里１'],
            '２里２': ['２里２'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            'Ｎ里': ['１里', '２里'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '１周': ['一周', '壹周', '一週', '壹週'],
            '２周': ['二周', '贰周', '二週', '贰週'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '１': ['蟬'],
            '２': ['蟬'],
            '⿱艹⿰虫单': ['⿱艹蟬'],
        })

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

        dest = StsMaker().make(config_file)
        self.assertEqual(dest, os.path.join(self.root, 'dict.list'))
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '陣': ['阵'],
            '噹': ['当'],
        })

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

        with self.assertRaises(RuntimeError):
            StsMaker().make(config_file)

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

        dest = StsMaker().make(config_file)
        self.assertEqual(dest, os.path.join(self.root, 'dict.list'))
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '陣': ['阵'],
            '噹': ['当'],
        })

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

        with self.assertRaises(RuntimeError):
            StsMaker().make(config_file)

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

        dest = StsMaker().make(config_file)
        self.assertEqual(dest, os.path.join(self.root, 'dict.list'))
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '陣': ['阵'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '简': ['簡'],
        })

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

        dest = StsMaker().make(config_file)
        stsdict = Table().load(dest)
        self.assertEqual(dict(stsdict), {
            '干': ['幹', '乾', '干'],
            '于': ['於'],
            '简': ['簡'],
        })

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

        with self.assertRaises(RuntimeError):
            StsMaker().make(config_file)

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

        dest = StsMaker().make(config_file)
        self.assertEqual(dest, os.path.join(self.root, 'dict.list'))
        with open(dest, encoding='UTF-8') as fh:
            self.assertEqual(fh.read(), '姜\t薑\n干\t幹 乾 干\n干姜\t乾薑\n')

    def test_dict_auto_space(self):
        config_file = os.path.join(self.root, 'config.json')
        with open(config_file, 'w', encoding='UTF-8') as fh:
            json.dump({
                'dicts': [
                    {
                        'file': 'dict.jlist',
                        'mode': 'load',
                        'src': [
                            'dict.json',
                        ],
                        'auto_space': True,
                    },
                ],
            }, fh)

        with open(os.path.join(self.root, 'dict.json'), 'w', encoding='UTF-8') as fh:
            json.dump({
                '干姜': ['乾薑'],
                '植物の优': ['植物の優'],
                '０只': ['０隻'],
                'Ｂ肝': ['Ｂ肝'],

                '1只': ['1隻'],
                '吃1只': ['吃1隻'],
                'SQL注入': ['SQL隱碼攻擊'],
                'A型⿰虫风': ['A型𧍯'],
                'A型刀劍󠄃': ['A型刀劍󠄃'],
            }, fh)

        dest = StsMaker().make(config_file)
        self.assertEqual(dest, os.path.join(self.root, 'dict.jlist'))
        stsdict = Table.loadjson(dest)
        self.assertEqual(dict(stsdict), {
            '干姜': ['乾薑'],
            '植物の优': ['植物の優'],
            '０只': ['０隻'],
            'Ｂ肝': ['Ｂ肝'],

            '1只': ['1隻'],
            '吃1只': ['吃1隻'],
            'SQL注入': ['SQL隱碼攻擊'],
            'A型⿰虫风': ['A型𧍯'],
            'A型刀劍󠄃': ['A型刀劍󠄃'],

            '1 只': ['1 隻'],
            '吃 1 只': ['吃 1 隻'],
            'SQL 注入': ['SQL 隱碼攻擊'],
            'A 型⿰虫风': ['A 型𧍯'],
            'A 型刀劍󠄃': ['A 型刀劍󠄃'],
        })

    def test_get_config_file(self):
        # absolute path
        self.assertEqual(
            StsMaker().get_config_file(os.path.join(self.root, 'myconf.json')),
            os.path.join(self.root, 'myconf.json'),
        )

        # relative to CWD
        self.assertEqual(
            StsMaker().get_config_file('myconf.json'),
            'myconf.json',
        )
        self.assertEqual(
            StsMaker().get_config_file('subdir/myconf.json'),
            os.path.normpath('subdir/myconf.json'),
        )

        # relative to base_dir
        self.assertEqual(
            StsMaker().get_config_file('myconf.json', base_dir=self.root),
            os.path.join(self.root, 'myconf.json'),
        )
        self.assertEqual(
            StsMaker().get_config_file('subdir/myconf.json', base_dir=self.root),
            os.path.normpath(os.path.join(self.root, 'subdir/myconf.json')),
        )

        # relative to default config directory
        tmpfile = os.path.join(StsMaker.config_dir, '__dummy__.tmp.json')
        with open(tmpfile, 'w'):
            pass
        try:
            self.assertEqual(
                StsMaker().get_config_file('__dummy__.tmp.json'),
                os.path.join(StsMaker.config_dir, '__dummy__.tmp.json'),
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
                        StsMaker().get_config_file('__dummy__.tmp'),
                        os.path.join(StsMaker.config_dir, f'__dummy__.tmp.{ext}'),
                    )
                finally:
                    os.remove(tmpfile)

    def test_get_stsdict_file(self):
        # absolute path
        self.assertEqual(
            StsMaker().get_stsdict_file(os.path.join(self.root, 'dict.list')),
            os.path.join(self.root, 'dict.list'),
        )

        # relative to CWD
        self.assertEqual(
            StsMaker().get_stsdict_file('dict.list'),
            'dict.list',
        )
        self.assertEqual(
            StsMaker().get_stsdict_file('subdir/dict.list'),
            os.path.normpath('subdir/dict.list'),
        )

        # relative to base_dir
        self.assertEqual(
            StsMaker().get_stsdict_file('dict.list', base_dir=self.root),
            os.path.join(self.root, 'dict.list'),
        )
        self.assertEqual(
            StsMaker().get_stsdict_file('subdir/dict.list', base_dir=self.root),
            os.path.normpath(os.path.join(self.root, 'subdir/dict.list')),
        )

        # relative to default dictionary directory
        tmpfile = os.path.join(StsMaker.dictionary_dir, '__dummy__.tmp.txt')
        with open(tmpfile, 'w'):
            pass
        try:
            self.assertEqual(
                StsMaker().get_stsdict_file('__dummy__.tmp.txt'),
                os.path.join(StsMaker.dictionary_dir, '__dummy__.tmp.txt'),
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
    @classmethod
    def setUpClass(cls):
        cls.sample_s2t_dict = Trie({
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

        cls.sample_s2twp_dict = Trie({
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
        self.assertEqual(dict(converter.table), {'干': ['幹', '乾', '干'], '干姜': ['乾薑']})
        self.assertIs(Trie, type(converter.table))

        # file as str (.jlist)
        tempfile = os.path.join(self.root, 'test.jlist')
        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""{"干": ["干", "榦"], "姜": ["姜", "薑"], "干姜": ["乾薑"]}""")
        converter = StsConverter(tempfile)
        self.assertEqual(dict(converter.table), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertIs(Trie, type(converter.table))

        # file as str (.tlist)
        tempfile = os.path.join(self.root, 'test.tlist')
        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""{"干": {"": ["干", "榦"], "姜": {"": ["乾薑"]}}, "姜": {"": ["姜", "薑"]}}""")
        converter = StsConverter(tempfile)
        self.assertEqual(dict(converter.table), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertIs(Trie, type(converter.table))

        # file as os.PathLike object
        tempfile = Path(os.path.join(self.root, 'test-path-like.list'))
        with open(tempfile, 'w', encoding='UTF-8') as fh:
            fh.write("""干\t幹 乾 干\n干姜\t乾薑""")
        converter = StsConverter(tempfile)
        self.assertEqual(dict(converter.table), {'干': ['幹', '乾', '干'], '干姜': ['乾薑']})
        self.assertIs(Trie, type(converter.table))

        # StsDict
        stsdict = Trie({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        converter = StsConverter(stsdict)
        self.assertEqual(dict(converter.table), {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        self.assertIs(stsdict, converter.table)

    def test_convert(self):
        converter = StsConverter(self.sample_s2t_dict)
        input = """干了 干涉 ⿱艹⿰虫风不需要简转繁"""
        expected = [(['干', '了'], ['幹了', '乾了']), ' ', (['干', '涉'], ['干涉']), ' ',
                    '⿱艹⿰虫风', '不', '需', '要', (['简'], ['簡']), (['转'], ['轉']), '繁']
        output = list(converter.convert(input))
        self.assertEqual(output, expected)

    def test_convert_exclude(self):
        converter = StsConverter(self.sample_s2t_dict)
        input = """-{尸}-廿山女田卜"""
        expected = [('尸',), '廿', '山', '女', '田', (['卜'], ['卜', '蔔'])]
        output = list(converter.convert(input, re.compile(r'-{(?P<return>.*?)}-')))
        self.assertEqual(output, expected)

        converter = StsConverter(self.sample_s2t_dict)
        input = """发财了<!-->财<--><!-->干<-->"""
        expected = [(['发', '财'], ['發財']), (['了'], ['了', '瞭']), ('财',), ('干',)]
        output = list(converter.convert(input, re.compile(r'<!-->(?P<return>.*?)<-->')))
        self.assertEqual(output, expected)

        converter = StsConverter(self.sample_s2twp_dict)
        input = """「奔馳」不是奔馳"""
        expected = [('「奔馳」',), '不', '是', (['奔', '馳'], ['賓士'])]
        output = list(converter.convert(input, re.compile(r'「.*?」')))
        self.assertEqual(output, expected)

        converter = StsConverter(self.sample_s2twp_dict)
        input = """奔-{}-驰"""  # noqa: P103
        expected = ['奔', (['驰'], ['馳'])]
        output = list(converter.convert(input, re.compile(r'-{(?P<return>.*?)}-')))  # noqa: P103
        self.assertEqual(output, expected)

        converter = StsConverter(self.sample_s2t_dict)
        input = """-{尸}-大口「发财了」"""
        expected = [('尸',), '大', '口', ('「发财了」',)]
        output = list(converter.convert(input, re.compile(r'「.*?」|-{(?P<return>.*?)}-')))
        self.assertEqual(output, expected)

        converter = StsConverter(self.sample_s2t_dict)
        input = """-{尸}-大口 <!-->财干<-->"""
        expected = [('尸',), '大', '口', ' ', ('财干',)]
        output = list(converter.convert(input, re.compile(r'-{(?P<return>.*?)}-|<!-->(?P<return2>.*?)<-->')))
        self.assertEqual(output, expected)

        converter = StsConverter(self.sample_s2twp_dict)
        input = """「奔馳」不是奔馳"""
        expected = [('「奔馳」',), '不', '是', (['奔', '馳'], ['賓士'])]
        output = list(converter.convert(input, re.compile(r'「(?P<nomatter>.*?)」')))
        self.assertEqual(output, expected)

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
        self.assertEqual(output, expected)

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
        self.assertEqual(output, expected)

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
        self.assertEqual(output, expected)

        # json
        expected = (
            r"""[[["干"],["幹","乾","干"]],"了"," ",[["干","涉"],["干涉"]],"\n","""
            r"""[["⿰虫风"],["𧍯"]],"需","要",[["简"],["簡"]],[["转"],["轉"]],"繁","\n","""
            r""""⿱艹⿰虫风","不","需","要",[["简"],["簡"]],[["转"],["轉"]],"繁","\n","""
            r"""[["沙","⿰虫风"],["沙虱"]],"也",[["简"],["簡"]],[["转"],["轉"]],"繁","\n"]"""
        )
        output = ''.join(converter.convert_formatted(input, 'json'))
        self.assertEqual(output, expected)

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
        self.assertNotEqual(output, expected)
        self.assertIn(expected, output)

        # template placeholders
        converter.htmlpage_template = io.StringIO('%CONTENT%')
        output = ''.join(converter.convert_formatted(input, 'htmlpage'))
        self.assertEqual(output, expected)

        converter.htmlpage_template = io.StringIO('%VERSION%')
        output = ''.join(converter.convert_formatted(input, 'htmlpage'))
        self.assertEqual(output, __version__)

        converter.htmlpage_template = io.StringIO('%%')
        output = ''.join(converter.convert_formatted(input, 'htmlpage'))
        self.assertEqual(output, '%')

    def test_convert_formatted_exclude(self):
        stsdict = self.sample_s2t_dict
        converter = StsConverter(stsdict)
        exclude = re.compile(r'-{(?P<return>.*?)}-')
        input = '-{尸}-廿山女田卜'

        # txt
        expected = '尸廿山女田卜'
        output = ''.join(converter.convert_formatted(input, 'txt', exclude))
        self.assertEqual(output, expected)

        # txtm
        expected = '尸廿山女田{{卜->卜|蔔}}'
        output = ''.join(converter.convert_formatted(input, 'txtm', exclude))
        self.assertEqual(output, expected)

        # html
        expected = '尸廿山女田<a atomic><del hidden>卜</del><ins>卜</ins><ins hidden>蔔</ins></a>'
        output = ''.join(converter.convert_formatted(input, 'html', exclude))
        self.assertEqual(output, expected)

        # json
        expected = '[["尸"],"廿","山","女","田",[["卜"],["卜","蔔"]]]'
        output = ''.join(converter.convert_formatted(input, 'json', exclude))
        self.assertEqual(output, expected)

    def test_convert_text(self):
        converter = StsConverter(self.sample_s2t_dict)
        input = """干了 干涉 ⿱艹⿰虫风不需要简转繁"""
        expected = r"""幹了 干涉 ⿱艹⿰虫风不需要簡轉繁"""
        self.assertEqual(converter.convert_text(input), expected)

    def test_convert_text_options(self):
        converter = StsConverter(Table())

        with mock.patch('sts.common.StsConverter.convert_formatted') as mocker:
            regex = re.compile(r'<!--(.*?)-->')
            converter.convert_text('乾柴', format='json', exclude=regex)
            mocker.assert_called_with('乾柴', format='json', exclude=regex)

        with mock.patch('sts.common.StsConverter.convert_formatted') as mocker:
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
        self.assertEqual(result, """乾柴烈火 發財圓夢""")

        # UTF-8 BOM should be preserved by default
        with open(tempfile, 'w', encoding='UTF-8-SIG') as fh:
            fh.write("""干柴烈火 发财圆梦""")
        converter.convert_file(tempfile, tempfile2)
        with open(tempfile2, 'r', encoding='UTF-8') as fh:
            result = fh.read()
        self.assertEqual(result, """\ufeff乾柴烈火 發財圓夢""")

        with open(tempfile, 'w', encoding='GBK') as fh:
            fh.write("""干柴烈火 发财圆梦""")
        converter.convert_file(tempfile, tempfile2, input_encoding='GBK', output_encoding='Big5')
        with open(tempfile2, 'r', encoding='Big5') as fh:
            result = fh.read()
        self.assertEqual(result, """乾柴烈火 發財圓夢""")

    def test_convert_file_fh(self):
        converter = StsConverter(self.sample_s2t_dict)
        fi = io.StringIO("""干柴烈火 发财圆梦""")
        fo = io.StringIO()
        converter.convert_file(fi, fo)
        result = fo.getvalue()
        self.assertEqual(result, """乾柴烈火 發財圓夢""")

    def test_convert_file_stdin(self):
        converter = StsConverter(self.sample_s2t_dict)
        fo = io.StringIO()
        with mock.patch('sys.stdin', io.StringIO("""干柴烈火 发财圆梦""")):
            converter.convert_file(None, fo)
        result = fo.getvalue()
        self.assertEqual(result, """乾柴烈火 發財圓夢""")

    def test_convert_file_stdout(self):
        converter = StsConverter(self.sample_s2t_dict)
        fi = io.StringIO("""干柴烈火 发财圆梦""")
        with redirect_stdout(io.StringIO()) as fh:
            converter.convert_file(fi)
        self.assertEqual(fh.getvalue(), """乾柴烈火 發財圓夢""")

    def test_convert_file_options(self):
        converter = StsConverter(Table())
        fi = io.StringIO('干姜')
        with mock.patch('sts.common.StsConverter.convert_formatted') as mocker:
            regex = re.compile(r'<!--(.*?)-->')
            converter.convert_file(fi, format='html', exclude=regex)
            mocker.assert_called_with('干姜', format='html', exclude=regex)


class TestStsConverterWithUnicode(unittest.TestCase):
    def test_ids(self):
        stsdict = Trie({
            '⿰虫风': ['𧍯'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual(converter.convert_text('虫风'), '虫风')
        self.assertEqual(converter.convert_text('⿰虫风'), '𧍯')
        self.assertEqual(converter.convert_text('⿱艹⿰虫风'), '⿱艹⿰虫风')
        self.assertEqual(converter.convert_text('⿱⿰虫风灬'), '⿱⿰虫风灬')

        stsdict = Trie({
            '虫': ['蟲'],
            '风': ['風'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual(converter.convert_text('虫风'), '蟲風')
        self.assertEqual(converter.convert_text('⿰虫风'), '⿰虫风')
        self.assertEqual(converter.convert_text('⿱艹⿰虫风'), '⿱艹⿰虫风')
        self.assertEqual(converter.convert_text('⿱⿰虫风灬'), '⿱⿰虫风灬')

    def test_ids_broken_at_non_hanzi(self):
        stsdict = Trie({
            '這': ['这'], '著': ['着'], '轉': ['转'], '簡': ['简'],
            '響': ['响'], '後': ['后'], '無': ['无'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual(
            converter.convert_text('IDC有這些：⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻，接著繁轉簡'),
            'IDC有这些：⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻，接着繁转简',
        )
        self.assertEqual(
            converter.convert_text('「⿰⿱⿲⿳」不影響後面'),
            '「⿰⿱⿲⿳」不影响后面',
        )
        self.assertEqual(
            converter.convert_text('⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻長度不夠\n這行無影響'),
            '⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻長度不夠\n这行无影响',
        )

    def test_vi(self):
        stsdict = Trie({
            '〾劍': ['剑'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual(converter.convert_text('刀劍'), '刀劍')
        self.assertEqual(converter.convert_text('刀〾劍'), '刀剑')

        stsdict = Trie({
            '劍': ['剑'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual(converter.convert_text('刀劍'), '刀剑')
        self.assertEqual(converter.convert_text('刀〾劍'), '刀〾劍')

    def test_vs(self):
        stsdict = Trie({
            '劍󠄁': ['剑'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual(converter.convert_text('刀劍'), '刀劍')
        self.assertEqual(converter.convert_text('刀劍󠄁'), '刀剑')
        self.assertEqual(converter.convert_text('刀劍󠄃'), '刀劍󠄃')
        self.assertEqual(converter.convert_text('刀劍󠄁󠄂'), '刀劍󠄁󠄂')

        stsdict = Trie({
            '劍': ['剑'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual(converter.convert_text('刀劍'), '刀剑')
        self.assertEqual(converter.convert_text('刀劍󠄁'), '刀劍󠄁')
        self.assertEqual(converter.convert_text('刀劍󠄃'), '刀劍󠄃')
        self.assertEqual(converter.convert_text('刀劍󠄁󠄂'), '刀劍󠄁󠄂')

    def test_cdm(self):
        stsdict = Trie({
            '黑桃Å': ['葵扇Å'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual(converter.convert_text('出黑桃A'), '出黑桃A')
        self.assertEqual(converter.convert_text('出黑桃Å'), '出黑桃Å')
        self.assertEqual(converter.convert_text('出黑桃Å'), '出葵扇Å')
        self.assertEqual(converter.convert_text('出黑桃À'), '出黑桃À')
        self.assertEqual(converter.convert_text('出黑桃Å̀'), '出黑桃Å̀')

        stsdict = Trie({
            '黑桃A': ['葵扇A'],
        })
        converter = StsConverter(stsdict)
        self.assertEqual(converter.convert_text('出黑桃A'), '出葵扇A')
        self.assertEqual(converter.convert_text('出黑桃Å'), '出黑桃Å')
        self.assertEqual(converter.convert_text('出黑桃Å'), '出黑桃Å')
        self.assertEqual(converter.convert_text('出黑桃À'), '出黑桃À')
        self.assertEqual(converter.convert_text('出黑桃Å̀'), '出黑桃Å̀')


if __name__ == '__main__':
    unittest.main()
