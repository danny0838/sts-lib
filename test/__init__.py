import unittest
import os
import re
import json
import time
from pathlib import Path
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
        d2 = Table(*args, **kwargs)
        d3 = Trie(*args, **kwargs)
        return d1, d2, d3

    def test_init(self):
        for class_ in (StsDict, Table, Trie):
            stsdict = class_({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
            self.assertEqual(stsdict, {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

            stsdict = class_(StsDict({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}))
            self.assertEqual(stsdict, StsDict({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}))

            stsdict = class_([('干', ['幹', '乾', '干']), ('姜', ['姜', '薑']), ('干姜', ['乾薑'])])
            self.assertEqual(stsdict, {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

            stsdict = class_(干=['幹', '乾', '干'], 姜=['姜', '薑'], 干姜=['乾薑'])
            self.assertEqual(stsdict, {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_repr(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}):
            self.assertEqual(eval(repr(stsdict)), stsdict)

    def test_getitem(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾', '干'], '豆干': ['豆乾']}):
            self.assertEqual(stsdict['干'], ['幹', '乾', '干'])
            self.assertEqual(stsdict['豆干'], ['豆乾'])
            with self.assertRaises(KeyError):
                stsdict['豆']
            with self.assertRaises(KeyError):
                stsdict['豆乾']

    def test_contains(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾', '干'], '豆干': ['豆乾']}):
            self.assertTrue('干' in stsdict)
            self.assertTrue('豆干' in stsdict)
            self.assertFalse('豆' in stsdict)
            self.assertFalse('豆乾' in stsdict)

    def test_len(self):
        for stsdict in self.prepare_dicts():
            self.assertEqual(len(stsdict), 0)
        for stsdict in self.prepare_dicts({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}):
            self.assertEqual(len(stsdict), 3)

    def test_iter(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾', '干'], '干姜': ['乾薑'], '姜': ['姜', '薑']}):
            self.assertEqual(set(stsdict), {'干', '姜', '干姜'})

    def test_eq(self):
        dict_ = {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']}
        for stsdict in self.prepare_dicts(dict_):
            self.assertTrue(stsdict == dict_)
            self.assertTrue(dict_ == stsdict)
            self.assertFalse(stsdict != dict_)
            self.assertFalse(dict_ != stsdict)

    def test_keys(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾', '干'], '干姜': ['乾薑'], '姜': ['姜', '薑']}):
            self.assertEqual(set(stsdict.keys()), {'干', '姜', '干姜'})

    def test_values(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾', '干'], '干姜': ['乾薑'], '姜': ['姜', '薑']}):
            self.assertEqual(set(tuple(x) for x in stsdict.values()), {('幹', '乾', '干'), ('姜', '薑'), ('乾薑',)})

    def test_items(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾'], '干姜': ['乾薑'], '姜': ['姜', '薑']}):
            self.assertEqual(dict(stsdict.items()), {'干': ['幹', '乾'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_add(self):
        for stsdict in self.prepare_dicts():
            stsdict.add('干', ['幹', '乾'])
            self.assertEqual(stsdict, {'干': ['幹', '乾']})
            stsdict.add('干', '干')
            self.assertEqual(stsdict, {'干': ['幹', '乾', '干']})
            stsdict.add('干', ['榦'])
            self.assertEqual(stsdict, {'干': ['幹', '乾', '干', '榦']})
            stsdict.add('姜', ['姜', '薑'])
            self.assertEqual(stsdict, {'干': ['幹', '乾', '干', '榦'], '姜': ['姜', '薑']})

    def test_add2(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾']}):
            stsdict.add('干', ['幹'])
            self.assertEqual(stsdict, {'干': ['幹', '乾']})
            stsdict.add('干', ['乾'], skip_check=True)
            self.assertEqual(stsdict, {'干': ['幹', '乾', '乾']})

    def test_update(self):
        for stsdict in self.prepare_dicts({'干': ['幹', '乾']}):
            dict_ = StsDict({'干': ['干'], '姜': ['姜', '薑']})
            stsdict.update(dict_)
            self.assertEqual(stsdict, {'干': ['幹', '乾', '干'], '姜': ['姜', '薑']})

            dict_ = {'干': ['干', '榦'], '干姜': ['乾薑']}
            stsdict.update(dict_)
            self.assertEqual(stsdict, {'干': ['幹', '乾', '干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_load(self):
        tempfile = os.path.join(root_dir, f"test-{time.time()}.tmp")
        tempfile2 = os.path.join(root_dir, f"test2-{time.time()}.tmp")
        try:
            with open(tempfile, 'w', encoding='UTF-8') as f:
                f.write("""干\t幹 乾""")
                f.close()
            with open(tempfile2, 'w', encoding='UTF-8') as f:
                f.write("""干\t干 榦\n姜\t姜 薑""")
                f.close()
            for stsdict in self.prepare_dicts():
                stsdict.load(tempfile, tempfile2)
                self.assertEqual(stsdict, {'干': ['幹', '乾', '干', '榦'], '姜': ['姜', '薑']})

            # check for cases of 0 or 2+ tabs
            with open(tempfile, 'w', encoding='UTF-8') as f:
                f.write("""干\t幹 乾\t# 一些註解\n姜\n干\t干\n\n干\t榦""")
                f.close()
            for stsdict in self.prepare_dicts():
                stsdict.load(tempfile)
                self.assertEqual(stsdict, {'干': ['幹', '乾', '干', '榦']})
        except:
            raise
        finally:
            try:
                os.remove(tempfile)
            except FileNotFoundError:
                pass
            try:
                os.remove(tempfile2)
            except FileNotFoundError:
                pass

    def test_dump(self):
        tempfile = os.path.join(root_dir, f"test-{time.time()}.tmp")
        try:
            for stsdict in self.prepare_dicts({'干': ['干', '榦'], '姜': ['姜', '薑']}):
                stsdict.dump(tempfile)
                with open(tempfile, 'r', encoding='UTF-8') as f:
                    text = f.read()
                self.assertEqual(text, '干\t干 榦\n姜\t姜 薑\n')

                stsdict.dump(tempfile, sort=True)
                with open(tempfile, 'r', encoding='UTF-8') as f:
                    text = f.read()
                self.assertEqual(text, '姜\t姜 薑\n干\t干 榦\n')
        except:
            raise
        finally:
            try:
                os.remove(tempfile)
            except FileNotFoundError:
                pass

    def test_loadjson(self):
        tempfile = os.path.join(root_dir, f"test-{time.time()}.tmp")
        try:
            with open(tempfile, 'w', encoding='UTF-8') as f:
                f.write('{"干": ["干", "榦"], "姜": ["姜", "薑"], "干姜": ["乾薑"]}')
            stsdict = StsDict().loadjson(tempfile)
            self.assertEqual(stsdict, {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

            with open(tempfile, 'w', encoding='UTF-8') as f:
                f.write('{"干": ["干", "榦"], "姜": ["姜", "薑"], "干姜": ["乾薑"]}')
            stsdict = Table().loadjson(tempfile)
            self.assertEqual(stsdict, {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

            with open(tempfile, 'w', encoding='UTF-8') as f:
                f.write('{"干": {"": ["干", "榦"], "姜": {"": ["乾薑"]}}, "姜": {"": ["姜", "薑"]}}')
            stsdict = Trie().loadjson(tempfile)
            self.assertEqual(stsdict, {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        except:
            raise
        finally:
            try:
                os.remove(tempfile)
            except FileNotFoundError:
                pass

    def test_dumpjson(self):
        tempfile = os.path.join(root_dir, f"test-{time.time()}.tmp")
        try:
            stsdict = StsDict({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
            stsdict.dumpjson(tempfile)
            with open(tempfile, 'r', encoding='UTF-8') as f:
                self.assertEqual(json.load(f), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

            stsdict = Table({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
            stsdict.dumpjson(tempfile)
            with open(tempfile, 'r', encoding='UTF-8') as f:
                self.assertEqual(json.load(f), {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

            stsdict = Trie({'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
            stsdict.dumpjson(tempfile)
            with open(tempfile, 'r', encoding='UTF-8') as f:
                self.assertEqual(json.load(f), {"干": {"": ["干", "榦"], "姜": {"": ["乾薑"]}}, "姜": {"": ["姜", "薑"]}})
        except:
            raise
        finally:
            try:
                os.remove(tempfile)
            except FileNotFoundError:
                pass

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
            stsdict2 = Table({'注': ['註', '注' ]})
            stsdict = stsdict._join_prefix(stsdict2)
            self.assertEqual(stsdict, {'注冊表': ['登錄檔'], '註冊表': ['登錄檔']})

        for stsdict in self.prepare_dicts({'註冊表': ['登錄檔']}):
            stsdict2 = Table({'注': ['注', '註'], '册': ['冊'], '注册': ['註冊']})
            stsdict = stsdict._join_prefix(stsdict2)
            self.assertEqual(stsdict, {'注册表': ['登錄檔'], '註冊表': ['登錄檔'], '註册表': ['登錄檔']})

    def test_postfix(self):
        for stsdict in self.prepare_dicts({'因为': ['因爲']}):
            stsdict2 = Table({'爲': ['為']})
            stsdict = stsdict._join_postfix(stsdict2)
            self.assertEqual(stsdict, {'因为': ['因為'], '爲': ['為']})

    def test_join(self):
        for stsdict in self.prepare_dicts({'则': ['則'], '达': ['達'], '规': ['規']}):
            stsdict2 = Table({'正則表達式': ['正規表示式'], '表達式': ['表示式']})
            stsdict = stsdict.join(stsdict2)
            self.assertEqual(stsdict, {
                '则': ['則'], '达': ['達'], '规': ['規'],
                '表達式': ['表示式'], '表达式': ['表示式'],
                '正則表達式': ['正規表示式'], '正则表达式': ['正規表示式'], '正则表達式': ['正規表示式'], '正則表达式': ['正規表示式']
                })

        for stsdict in self.prepare_dicts({
            '万用字元': ['萬用字元'], '数据': ['數據'],
            '万': ['萬', '万'], '数': ['數'], '据': ['據', '据'], '问': ['問'], '题': ['題'],
            }):
            stsdict2 = Table({'元數據': ['後設資料'], '數據': ['資料']})
            stsdict = stsdict.join(stsdict2)
            self.assertEqual(stsdict, {
                '万用字元': ['萬用字元'], '数据': ['資料'],
                '万': ['萬', '万'], '数': ['數'], '据': ['據', '据'], '问': ['問'], '题': ['題'],
                '元數據': ['後設資料'], '數據': ['資料'],
                '元数据': ['後設資料'], '元数據': ['後設資料'], '元數据': ['後設資料'],
                '数據': ['資料'], '數据': ['資料'],
                })

        for stsdict in self.prepare_dicts({'妳': ['你', '奶']}):
            stsdict2 = Table({'奶媽': ['奶娘']})
            stsdict = stsdict.join(stsdict2)
            self.assertEqual(stsdict, {
                '妳': ['你', '奶'],
                '奶媽': ['奶娘'],
                })


class TestClassStsListMaker(unittest.TestCase):
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
    def test_init(self):
        # file as str (.list)
        tempfile = os.path.join(root_dir, f"test-{time.time()}.list")
        try:
            with open(tempfile, 'w', encoding='UTF-8') as f:
                f.write("""干\t幹 乾 干\n干姜\t乾薑""")
                f.close()
            converter = StsConverter(tempfile)
            self.assertEqual(converter.table, {'干': ['幹', '乾', '干'], '干姜': ['乾薑']})
        except:
            raise
        finally:
            try:
                os.remove(tempfile)
            except FileNotFoundError:
                pass

        # file as str (.jlist)
        tempfile = os.path.join(root_dir, f"test-{time.time()}.jlist")
        try:
            with open(tempfile, 'w', encoding='UTF-8') as f:
                f.write("""{"干": ["干", "榦"], "姜": ["姜", "薑"], "干姜": ["乾薑"]}""")
                f.close()
            converter = StsConverter(tempfile)
            self.assertEqual(converter.table, {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        except:
            raise
        finally:
            try:
                os.remove(tempfile)
            except FileNotFoundError:
                pass

        # file as str (.tlist)
        tempfile = os.path.join(root_dir, f"test-{time.time()}.tlist")
        try:
            with open(tempfile, 'w', encoding='UTF-8') as f:
                f.write("""{"干": {"": ["干", "榦"], "姜": {"": ["乾薑"]}}, "姜": {"": ["姜", "薑"]}}""")
                f.close()
            converter = StsConverter(tempfile)
            self.assertEqual(converter.table, {'干': ['干', '榦'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        except:
            raise
        finally:
            try:
                os.remove(tempfile)
            except FileNotFoundError:
                pass

        # file as os.PathLike object
        tempfile = Path(os.path.join(root_dir, f"test-{time.time()}.list"))
        try:
            with open(tempfile, 'w', encoding='UTF-8') as f:
                f.write("""干\t幹 乾 干\n干姜\t乾薑""")
                f.close()
            converter = StsConverter(tempfile)
            self.assertEqual(converter.table, {'干': ['幹', '乾', '干'], '干姜': ['乾薑']})
        except:
            raise
        finally:
            try:
                os.remove(tempfile)
            except FileNotFoundError:
                pass

        # StsDict
        stsdict = Trie({'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})
        converter = StsConverter(stsdict)
        self.assertEqual(converter.table, {'干': ['幹', '乾', '干'], '姜': ['姜', '薑'], '干姜': ['乾薑']})

    def test_convert(self):
        stsdict = StsListMaker().make('s2t', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual(
            list(converter.convert("""干了 干涉
⿰虫风需要简转繁
⿱艹⿰虫风不需要简转繁
沙⿰虫风也简转繁""")),
            [(['干', '了'], ['幹了', '乾了']), ' ', (['干', '涉'], ['干涉']), '\n',
            '⿰虫风', '需', '要', (['简'], ['簡']), (['转'], ['轉']), '繁', '\n',
            '⿱艹⿰虫风', '不', '需', '要', (['简'], ['簡']), (['转'], ['轉']), '繁', '\n',
            '沙', '⿰虫风', '也', (['简'], ['簡']), (['转'], ['轉']), '繁'])

    def test_convert_text(self):
        stsdict = StsListMaker().make('s2t', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual(
            converter.convert_text("""干了 干涉
⿰虫风需要简转繁
⿱艹⿰虫风不需要简转繁
沙⿰虫风也简转繁"""),
            r"""幹了 干涉
⿰虫风需要簡轉繁
⿱艹⿰虫风不需要簡轉繁
沙⿰虫风也簡轉繁""")

    def test_convert_file(self):
        tempfile = os.path.join(root_dir, f"test-{time.time()}.tmp")
        tempfile2 = os.path.join(root_dir, f"test2-{time.time()}.tmp")
        try:
            stsdict = StsListMaker().make('s2t', quiet=True)
            converter = StsConverter(stsdict)

            with open(tempfile, 'w', encoding='UTF-8') as f:
                f.write("""干柴烈火 发财圆梦""")
                f.close()
            converter.convert_file(tempfile, tempfile2)
            with open(tempfile2, 'r', encoding='UTF-8') as f:
                result = f.read()
                f.close()
            self.assertEqual(result, """乾柴烈火 發財圓夢""")

            with open(tempfile, 'w', encoding='GBK') as f:
                f.write("""干柴烈火 发财圆梦""")
                f.close()
            converter.convert_file(tempfile, tempfile2, input_encoding='GBK', output_encoding='Big5')
            with open(tempfile2, 'r', encoding='Big5') as f:
                result = f.read()
                f.close()
            self.assertEqual(result, """乾柴烈火 發財圓夢""")
        except:
            raise
        finally:
            try:
                os.remove(tempfile)
            except FileNotFoundError:
                pass
            try:
                os.remove(tempfile2)
            except FileNotFoundError:
                pass

    def test_convert_option_format(self):
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
        text = r"""干了 干涉
⿰虫风需要简转繁
⿱艹⿰虫风不需要简转繁
沙⿰虫风也简转繁"""

        converter = StsConverter(stsdict, options={'format': 'txt'})
        self.assertEqual(
            converter.convert_text(text),
            r"""幹了 干涉
𧍯需要簡轉繁
⿱艹⿰虫风不需要簡轉繁
沙虱也簡轉繁"""
            )

        converter = StsConverter(stsdict, options={'format': 'txtm'})
        self.assertEqual(
            converter.convert_text(text),
            r"""{{干->幹|乾|干}}了 {{干涉}}
{{⿰虫风->𧍯}}需要{{简->簡}}{{转->轉}}繁
⿱艹⿰虫风不需要{{简->簡}}{{转->轉}}繁
{{沙⿰虫风->沙虱}}也{{简->簡}}{{转->轉}}繁"""
            )

        converter = StsConverter(stsdict, options={'format': 'html'})
        self.assertEqual(
            converter.convert_text(text),
            r"""<span class="sts-conv plural atomic"><del>干</del><ins>幹</ins><ins>乾</ins><ins>干</ins></span>了 <span class="sts-conv single exact"><del>干涉</del><ins>干涉</ins></span>
<span class="sts-conv single atomic"><del>⿰虫风</del><ins>𧍯</ins></span>需要<span class="sts-conv single atomic"><del>简</del><ins>簡</ins></span><span class="sts-conv single atomic"><del>转</del><ins>轉</ins></span>繁
⿱艹⿰虫风不需要<span class="sts-conv single atomic"><del>简</del><ins>簡</ins></span><span class="sts-conv single atomic"><del>转</del><ins>轉</ins></span>繁
<span class="sts-conv single"><del>沙⿰虫风</del><ins>沙虱</ins></span>也<span class="sts-conv single atomic"><del>简</del><ins>簡</ins></span><span class="sts-conv single atomic"><del>转</del><ins>轉</ins></span>繁"""
            )

        converter = StsConverter(stsdict, options={'format': 'json'})
        self.assertEqual(
            converter.convert_text(text),
            r"""[[["干"], ["幹", "乾", "干"]], "了", " ", [["干", "涉"], ["干涉"]], "\n", [["⿰虫风"], ["𧍯"]], "需", "要", [["简"], ["簡"]], [["转"], ["轉"]], "繁", "\n", "⿱艹⿰虫风", "不", "需", "要", [["简"], ["簡"]], [["转"], ["轉"]], "繁", "\n", [["沙", "⿰虫风"], ["沙虱"]], "也", [["简"], ["簡"]], [["转"], ["轉"]], "繁"]"""
            )

    def test_convert_option_exclude(self):
        stsdict = StsListMaker().make('s2t', quiet=True)
        converter = StsConverter(stsdict, options={'exclude': r'-{(?P<return>.*?)}-'})
        self.assertEqual(converter.convert_text(r"""-{尸}-廿山女田卜"""), r"""尸廿山女田卜""")

        stsdict = StsListMaker().make('s2t', quiet=True)
        converter = StsConverter(stsdict, options={'exclude': r'<!-->(?P<return>.*?)<-->'})
        self.assertEqual(converter.convert_text(r"""发财了<!-->财<--><!-->干<-->"""), r"""發財了财干""")

        stsdict = StsListMaker().make('s2twp', quiet=True)
        converter = StsConverter(stsdict, options={'exclude': r'「.*?」'})
        self.assertEqual(converter.convert_text(r"""「奔馳」不是奔馳"""), r"""「奔馳」不是賓士""")


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
        self.assertEqual(converter.convert_text('⿰虫风简转繁不会出错'), '⿰虫风簡轉繁不會出錯')
        self.assertEqual(converter.convert_text('⿱艹⿰虫风简转繁不会出错'), '⿱艹⿰虫风簡轉繁不會出錯')

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
        self.assertEqual(converter.convert_text('⿰虫风需要简转繁'), '𧍯需要簡轉繁')
        self.assertEqual(converter.convert_text('⿱艹⿰虫风不需要简转繁'), '⿱艹⿰虫风不需要簡轉繁')

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
        self.assertEqual(converter.convert_text('⿰虫风不需要简转繁'), '⿰虫风不需要簡轉繁')
        self.assertEqual(converter.convert_text('⿱艹⿰虫风需要简转繁'), '⿱艹𧍯需要簡轉繁')

    def test_ids_broken(self):
        stsdict = StsListMaker().make('tw2s', quiet=True)
        converter = StsConverter(stsdict)
        self.assertEqual(converter.convert_text('IDC有這些：⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻，接著繁轉簡'), 'IDC有这些：⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻，接着繁转简')
        self.assertEqual(converter.convert_text('「⿰⿱⿲⿳」不影響後面'), '「⿰⿱⿲⿳」不影响后面')
        self.assertEqual(converter.convert_text('⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻長度不夠\n這行無影響'), '⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻長度不夠\n这行无影响')

    def test_vi(self):
        stsdict = Trie({
            '劍': ['剑'],
            '〾劍': ['剑'],
            '訢': ['欣', '䜣'],
            '劍訢': ['剑䜣'],
            })
        converter = StsConverter(stsdict)
        self.assertEqual(converter.convert_text('刀劍 劍訢'), '刀剑 剑䜣')
        self.assertEqual(converter.convert_text('刀〾劍 〾劍訢 劍〾訢 〾劍〾訢'), '刀剑 剑欣 剑〾訢 剑〾訢')

    def test_vs(self):
        stsdict = Trie({
            '劍': ['剑'],
            '劍󠄁': ['剑'],
            '訢': ['欣', '䜣'],
            '劍訢': ['剑䜣'],
            })
        converter = StsConverter(stsdict)
        self.assertEqual(converter.convert_text('刀劍 劍訢'), '刀剑 剑䜣')
        self.assertEqual(converter.convert_text('刀劍󠄁 劍󠄁訢'), '刀剑 剑欣')
        self.assertEqual(converter.convert_text('刀劍󠄃 劍󠄃訢'), '刀劍󠄃 劍󠄃欣')
        self.assertEqual(converter.convert_text('刀劍󠄁󠄂 劍󠄁󠄂訢'), '刀劍󠄁󠄂 劍󠄁󠄂欣')

    def test_cdm(self):
        stsdict = Trie({
            '黑桃A': ['葵扇A'],
            '黑桃Å': ['扇子Å'],
            })
        converter = StsConverter(stsdict)
        self.assertEqual(converter.convert_text('出黑桃A'), '出葵扇A')
        self.assertEqual(converter.convert_text('出黑桃Å'), '出扇子Å')
        self.assertEqual(converter.convert_text('出黑桃A̧'), '出黑桃A̧')
        self.assertEqual(converter.convert_text('出黑桃Å̧'), '出黑桃Å̧')

        stsdict = Trie({
            'A片': ['成人片'],
            'Å片': ['特製成人片'],
            })
        converter = StsConverter(stsdict)
        self.assertEqual(converter.convert_text('看A片'), '看成人片')
        self.assertEqual(converter.convert_text('看Å片'), '看特製成人片')
        self.assertEqual(converter.convert_text('看A̧片'), '看A̧片')
        self.assertEqual(converter.convert_text('看Å̧片'), '看Å̧片')


class TestConfigs(unittest.TestCase):
    @unittest.skip
    def test_make(self):
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
