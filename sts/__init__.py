#!/usr/bin/env python3
"""An open library for simplified-traditional Chinese text conversion.
"""
import sys
import os
import re
import glob
import argparse
import json
import html
from collections import namedtuple, OrderedDict
import math

__version__ = '0.16.0'
__author__ = 'Danny Lin'
__author_email__ = 'danny0838@gmail.com'
__homepage__ = 'https://github.com/danny0838/sts-lib'
__license__ = 'Apache 2.0'

StsDictMatch = namedtuple('StsDictMatch', ['conv', 'start', 'end'])
StsDictConv = namedtuple('StsDictConv', ['key', 'values'])

def lazyprop(fn):
    """Lazy property decorator

    Defines a lazy property that is evaluated only for the first time,
    and can be modified (set) or invalidated (del).

    Modified from: https://github.com/sorin/lazyprop
    """
    attr_name = '_lazy_' + fn.__name__

    @property
    def _lazyprop(self):
        try:
            return getattr(self, attr_name)
        except AttributeError:
            value = fn(self)
            setattr(self, attr_name, value)
            return value

    @_lazyprop.deleter
    def _lazyprop(self):
        try:
            delattr(self, attr_name)
        except AttributeError:
            pass

    @_lazyprop.setter
    def _lazyprop(self, value):
        setattr(self, attr_name, value)

    return _lazyprop

class Unicode():
    """Utilities for Unicode string handling.
    """
    @staticmethod
    def composite_length(text, pos):
        """Get the length of the Unicode composite at pos.

        A unicode composite is a complex of characters with composers.
        For example, an ideographic description sequence (IDS),
        or a hanzi with a variant selector (VS), etc.
        """
        i = pos
        total = len(text)
        length = 1
        is_ids = False

        while length and i < total:
            code = ord(text[i])

            # check if the current char is a prefix composer
            if code == 0x303E:
                # ideographic variation indicator
                is_ids = True
                length += 1
            elif 0x2FF0 <= code <= 0x2FF1 or 0x2FF4 <= code <= 0x2FFB:
                # IDS binary operator
                is_ids = True
                length += 2
            elif 0x2FF2 <= code <= 0x2FF3:
                # IDS trinary operator
                is_ids = True
                length += 3
            elif is_ids and not (0x4E00 <= code <= 0x9FFF  # CJK unified
                    or 0x3400 <= code <= 0x4DBF or 0x20000 <= code <= 0x3FFFF  # Ext-A, ExtB+
                    or 0xF900 <= code <= 0xFAFF or 0x2F800 <= code <= 0x2FA1F  # Compatibility
                    or 0x2E80 <= code <= 0x2FDF  # Radical
                    or 0x31C0 <= code <= 0x31EF  # Stroke
                    or 0xE000 <= code <= 0xF8FF or 0xF0000 <= code <= 0x1FFFFF  # Private
                    or code == 0xFF1F  # ？
                    or 0xFE00 <= code <= 0xFE0F or 0xE0100 <= code <= 0xE01EF  # VS
                    ):
                # check for a valid IDS to avoid a breaking on e.g.:
                #
                #     IDS包括⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻，可用於…
                #
                # - IDS := Ideographic | Radical | CJK_Stroke | Private Use
                #        | U+FF1F | IDS_BinaryOperator IDS IDS
                #        | IDS_TrinaryOperator IDS IDS IDS
                #
                # - We also allow IVI and VS in an IDS.
                break

            # check if the next char is a postfix composer
            if i + 1 < total:
                code = ord(text[i + 1])
                if 0xFE00 <= code <= 0xFE0F:
                    # variation selectors
                    length += 1
                elif 0xE0100 <= code <= 0xE01EF:
                    # variation selectors supplement
                    length += 1
                elif 0x180B <= code <= 0x180D:
                    # Mongolian free variation selectors
                    length += 1
                elif 0x0300 <= code <= 0x036F:
                    # combining diacritical marks
                    length += 1
                elif 0x1AB0 <= code <= 0x1AFF:
                    # combining diacritical marks extended
                    length += 1
                elif 0x1DC0 <= code <= 0x1DFF:
                    # combining diacritical marks supplement
                    length += 1
                elif 0x20D0 <= code <= 0x20FF:
                    # combining diacritical marks for symbols
                    length += 1
                elif 0xFE20 <= code <= 0xFE2F:
                    # combining half marks
                    length += 1

            i += 1
            length -= 1

        return i - pos

    @staticmethod
    def split(text):
        """Split text into a list of Unicode composites.
        """
        i = 0
        total = len(text)
        result = []
        while i < total:
            length = Unicode.composite_length(text, i)
            result.append(text[i:i + length])
            i += length
        return result

class StsDict(OrderedDict):
    """Base class of an STS dictionary.

    This class is for child classes to implement on and not intended to be
    used directly.

    Supported serializations are:
    - plain-dict: which is a text file that looks like:

          key1 <tab> value1-1 [<space> value1-2 <space> ...]
          key2 <tab> value2-1 [<space> value2-2 <space> ...]
          ...

    - JSON: which is dumped from the internal data structure.

    NOTE: The internal data structure may vary across subclasses. As a result,
    loadjson(), dumpjson(), and most native dict methods like __init__(),
    __iter__(), items(), keys(), and values() work on their own format.

    To safely create a subclass from a dict-compatible data format, do
    something like:

        SubClass().add_dict(StsDict(...))

    Or use load() or load_filegroups() to load from a plain-dict file.
    """
    def iter(self):
        """Get a generator of key-values pairs.
        """
        yield from self.items()

    def add(self, key, values, skip_check=False):
        """Add a key-values pair to this dictionary.

        Args:
            values: a string or a list of strings.
            skip_check: True to skip checking duplicated values.
        """
        values = [values] if isinstance(values, str) else values
        list_ = self.setdefault(key, [])
        if skip_check:
            list_ += values
        else:
            list_ += [x for x in values if x not in list_]
        return self

    def add_dict(self, stsdict, skip_check=False):
        """Add all key-values pairs from another StsDict.

        Args:
            skip_check: True to skip checking duplicated values.
        """
        for key, values in stsdict.iter():
            self.add(key, values, skip_check=skip_check)
        return self

    def load(self, *files):
        """Add all key-values pairs from plain-dict file(s).
        """
        for file in files:
            with open(file, "r", encoding="UTF-8") as f:
                for line in f:
                    parts = line.strip().split("\t")
                    if len(parts) > 1:
                        key, values = parts[0], parts[1]
                        self.add(key, values.split(" "))
                f.close()
        return self

    def dump(self, file=None, sort=False):
        """Dump key-values pairs to a plain-dict file.

        Args:
            file: path of file to save. Use stdout if None.
            sort: True to sort the output.
        """
        f = open(file, "w", encoding="UTF-8", newline="") if file else sys.stdout
        iterator = self.iter()
        if sort: iterator = sorted(iterator)
        for key, values in iterator:
            f.write(f'{key}\t{" ".join(values)}\n')
        if f is not sys.stdout: f.close()

    def loadjson(self, file):
        """Load from a JSON file.

        NOTE: The input data format may vary across subclasses.

        Returns:
            a new object with the same class.
        """
        with open(file, 'r', encoding='UTF-8') as f:
            stsdict = self.__class__(json.load(f))
            f.close()
        return stsdict

    def dumpjson(self, file=None, indent=None, sort=False):
        """Dump key-values pairs to a JSON file.

        NOTE: The output data format may vary across subclasses.

        Args:
            file: path of file to save. Use stdout if None.
            indent: indent the output with a specified integer.
            sort: True to sort the output.
        """
        f = open(file, "w", encoding="UTF-8", newline="") if file else sys.stdout
        json.dump(self, f, ensure_ascii=False, indent=indent, sort_keys=sort)
        if f is not sys.stdout: f.close()

    def print(self, sort=False):
        """Print key-values pairs.

        Args:
            sort: True to sort the output.
        """
        iterator = self.iter()
        if sort: iterator = sorted(iterator)
        for key, values in iterator:
            print(f'{key} => {" ".join(values)}')

    def find(self, keyword, from_keys=True, from_values=True, exact=False):
        """Search for keyword from the dictionary.

        Args:
            from_keys: True to search from keys.
            from_values: True to search from values.
            exact: True to force exact match of a value with a keyword.

        Returns:
            a generator of matched key-values pairs.
        """
        for key, values in self.iter():
            if exact:
                if from_keys and keyword == key:
                    yield key, values
                elif from_values and keyword in values:
                    yield key, values
            else:
                if from_keys and keyword in key:
                    yield key, values
                elif from_values:
                    for value in values:
                        if keyword in value:
                            yield key, values

    def swap(self):
        """Swap the keys and values of the dictionary.

        Returns:
            a new object with the same class.
        """
        stsdict = self.__class__()
        for key, values in self.iter():
            for value in values:
                stsdict.add(value, key)
        return stsdict

    def load_filegroups(self, filegroups):
        """Load key-values pairs from a list of plain-dict files.

        Args:
            filegroups: a list of plain-dict files.
            [
                [file1-1, file1-2, ...]
                [file2-1, file2-2, file2-3, ...]
                [file3-1, file3-2, file3-3, ...]
            ]

        Returns:
            a new object with the same class.
        """
        stsdicts = [self.__class__().load(*files) for files in filegroups]
        newstsdict = self
        while len(stsdicts):
            newstsdict = newstsdict.join(stsdicts.pop(0))
        return newstsdict

    def join(self, stsdict):
        """Join another dictionary.

        Applying the returned dictionary to a text simulates the effect
        of applying using self and then using stsdict.

        Returns:
            a new object with the same class.
        """
        dict1 = self._join_postfix(stsdict)
        dict2 = stsdict._join_prefix(self)
        return dict1.add_dict(dict2)

    def _join_prefix(self, stsdict):
        """Prefix self with stsdict.

        Convert keys of self using swapped stsdict.
        (Enumerate all potential matches.)

        Returns:
            a new object with the same class.

        e.g.
        table:
            註冊表 => 登錄檔
        stsdict:
            注 => 注 註
        swapped stsdict:
            注 => 注
            註 => 注
        table._join_prefix(stsdict):
            注冊表 => 登錄檔
            註冊表 => 登錄檔
        """
        dict_ = self.__class__()
        converter = stsdict.swap()
        for key, values in self.iter():
            for newkey in converter.apply_enum(key, include_short=True, include_self=True):
                dict_.add(newkey, values)
        return dict_

    def _join_postfix(self, stsdict):
        """Postfix self with stsdict.

        Convert values of self using stsdict.
        (Enumerate maximal matches.)

        Returns:
            a new object with the same class.

        e.g.
        table:
            因为 => 因爲
        stsdict:
            爲 => 為
        table._join_postfix(stsdict):
            因为 => 因為
            爲 => 為
        """
        dict_ = self.__class__()
        for key, values in self.iter():
            for value in values:
                dict_.add(key, stsdict.apply_enum(value))
        dict_.add_dict(stsdict)
        return dict_

    def match(self, parts, pos, maxlen=math.inf):
        """Match a unicode composite at pos.

        Args:
            parts: a string or iterable parts to be matched.

        Returns:
            an StsDictMatch or None if no match.
        """
        parts = (Unicode.split(parts) if isinstance(parts, str) else
                parts if isinstance(parts, list) else
                list(parts))
        i = max(len(Unicode.split(key)) for key in self)
        i = min(i, min(len(parts), maxlen) - pos)
        while i >= 1:
            end = pos + i
            current_parts = parts[pos:end]
            current = "".join(current_parts)
            if current in self:
                conv = StsDictConv(current_parts, self[current])
                return StsDictMatch(conv, pos, end)
            i -= 1
        return None

    def apply(self, parts):
        """Convert text using the dictionary.

        Args:
            parts: a string or iterable parts to be converted.

        Returns:
             a generator of parts, which is a string or an StsDictConv.
        """
        parts = (Unicode.split(parts) if isinstance(parts, str) else
                parts if isinstance(parts, list) else
                list(parts))
        i = 0
        total = len(parts)
        while i < total:
            match = self.match(parts, i)
            if match is not None:
                yield match.conv
                i = match.end
            else:
                yield parts[i]
                i += 1

    def apply_enum(self, parts, include_short=False, include_self=False):
        """Enumerate all possible conversions of text.

        Args:
            parts: a string or iterable parts to be converted.
            include_short: include non-maximal-match conversions
            include_self: include source for every match

        Returns:
            list: a list of possible conversions.

        e.g.
        table:
            钟 => 鐘 鍾
            药 => 藥 葯
            用药 => 用藥
        text:
            '看钟用药'
        table.apply_enum(text, include_short=False, include_self=False):
            ['看鐘用藥', '看鍾用藥']
        table.apply_enum(text, include_short=True, include_self=False):
            ['看鐘用藥', '看鐘用葯', '看鍾用藥', '看鍾用葯']
        table.apply_enum(text, include_short=False, include_self=True):
            ['看鐘用藥', '看鐘用药', '看鍾用藥', '看鍾用药', '看钟用藥', '看钟用药']
        table.apply_enum(text, include_short=True, include_self=True):
            ['看鐘用藥', '看鐘用药', '看鐘用葯', '看鍾用藥', '看鍾用药', '看鍾用葯', '看钟用藥', '看钟用药', '看钟用葯']
        """
        if isinstance(parts, str):
            text = parts
            parts = Unicode.split(parts)
        elif isinstance(parts, list):
            text = None
        else:
            text = None
            parts = list(parts)

        queue = [(parts, 0, 0)]
        subqueue = []
        results = OrderedDict()
        while len(queue):
            (parts, matched, nextindex) = data = queue.pop()
            if nextindex < len(parts):
                self._apply_enum_sub(subqueue, data, include_short=include_short, include_self=include_self)
                while len(subqueue):
                    queue.append(subqueue.pop())
            elif matched > 0:
                results["".join(parts)] = True

        results = list(results)

        if len(results) == 0:
            results.append(text if text is not None else "".join(parts))

        return results

    def _apply_enum_sub(self, queue, data, include_short=False, include_self=False):
        """Helper function of apply_enum
        """
        (parts, matched, index) = data
        match = self.match(parts, index)

        # add atomic stepping if no match
        if match is None:
            queue.append((parts, matched, index + 1))
            return

        has_atomic_match = False
        if match.end - index == 1:
            has_atomic_match = True
        if include_self:
            match_key = ''.join(match.conv.key)
            if match_key not in match.conv.values:
                match.conv.values.append(match_key)
        for value in match.conv.values:
            result = parts[:index] + [value] + parts[match.end:]
            queue.append((result, matched + 1, index + 1))

        if not include_short:
            return

        # add shorter matches
        for i in range(match.end - match.start - 1, 0, -1):
            match = self.match(parts, index, maxlen=index + i)
            if match is not None:
                if match.end - index == 1:
                    has_atomic_match = True
                if include_self:
                    match_key = ''.join(match.conv.key)
                    if match_key not in match.conv.values:
                        match.conv.values.append(match_key)
                for value in match.conv.values:
                    result = parts[:index] + [value] + parts[match.end:]
                    queue.append((result, matched + 1, index + 1))

        # add atomic stepping (length = 1) case
        #
        # e.g.
        # table: 采信 => 採信, 信息 => 訊息
        # text: ["采", "信", "息"]
        #
        # We get a match ["采", "信", "息"] but no atomic match available.
        #                 ^^^^^^^^^^
        #
        # Add ["采", "信", "息"] so that "采訊息" is not missed.
        #             ^
        if not has_atomic_match:
            queue.append((parts, matched, index + 1))

class Table(StsDict):
    """A cache-boosted STS dictionary.

    This class implements a cache and a head-char checking mechanism to
    improve performance on text conversion than base StsDict.

    The internal data format is same as base StsDict.

    NOTE: The cache will not update after generated, and therefore the
    dictionary should not be modified after performing a text matching or
    conversion (match, apply, apply_enum, etc.) to avoid an unexpected
    behavior.
    """
    @lazyprop
    def key_maxlen(self):
        """Get the maximal length of the keys.
        """
        return max(len(Unicode.split(key)) for key in self)

    @lazyprop
    def key_headchars(self):
        """Get a set of the first char of the keys.
        """
        return set(key[0] for key in self)

    def match(self, parts, pos, maxlen=math.inf):
        """Match a unicode composite at pos.

        Args:
            parts: a string or iterable parts to be matched.

        Returns:
            an StsDictMatch or None if no match.
        """
        parts = (Unicode.split(parts) if isinstance(parts, str) else
                parts if isinstance(parts, list) else
                list(parts))
        if parts[pos][0] in self.key_headchars:
            i = self.key_maxlen
            i = min(i, min(len(parts), maxlen) - pos)
            while i >= 1:
                end = pos + i
                current_parts = parts[pos:end]
                current = "".join(current_parts)
                if current in self:
                    conv = StsDictConv(current_parts, self[current])
                    return StsDictMatch(conv, pos, end)
                i -= 1
        return None

class Trie(StsDict):
    """An STS dictionary with trie (prefix tree) format.

    Compared with hash, trie is faster for applying conversion,
    but takes more space and is slower to construct.

    NOTE: The internal data format is different from base StsDict.
    """
    def iter(self):
        """Get a generator of key-values pairs.
        """
        def recurse(trie):
            for key in trie:
                if key == "":
                    yield ''.join(keystack), trie[key]
                else:
                    keystack.append(key)
                    triestack.append(trie[key])
                    yield from recurse(triestack[-1])
            keystack.pop()
            triestack.pop()

        keystack = [""]
        triestack = [self]
        yield from recurse(triestack[-1])

    def add(self, key, values, skip_check=False):
        """Add a key-values pair to this dictionary.

        Args:
            values: a string or a list of strings.
            skip_check: True to skip checking duplicated values.
        """
        values = [values] if isinstance(values, str) else values

        current = self
        for i, composite in enumerate(Unicode.split(key)):
            current = current.setdefault(composite, OrderedDict())

        list_ = current.setdefault('', [])
        if skip_check:
            list_ += values
        else:
            list_ += [x for x in values if x not in list_]
        return self

    def match(self, parts, pos, maxlen=math.inf):
        """Match a unicode composite at pos.

        Args:
            parts: a string or iterable parts to be matched.

        Returns:
            an StsDictMatch or None if no match.
        """
        parts = (Unicode.split(parts) if isinstance(parts, str) else
                parts if isinstance(parts, list) else
                list(parts))
        trie = self
        i = pos
        total = min(len(parts), maxlen)
        match = None
        match_end = None
        while i < total:
            key = parts[i]
            if key not in trie:
                break
            trie = trie[key]
            if "" in trie:
                match = trie[""]
                match_end = i + 1
            i = i + 1
        if match:
            conv = StsDictConv(parts[pos:match_end], match)
            return StsDictMatch(conv, pos, match_end)
        return None

class StsListMaker():
    """A class for compling a dictionary.
    """
    def make(self, config_name, base_dir=None, output_dir=None, skip_requires=False, quiet=False):
        """Compile a dictionary according to config.

        Load dictionaries specified in config and generate a new dictionary.

        scheme of config (.json):
        {
            "name": "...",
            "requires": [
                "..."  // a required config (relative to this config file)
            ],
            "dicts": [{
                "file": "...",  // relative to default config directory
                "type": "...",  // list, jlist, tlist
                "mode": "...",  // load, swap, join
                "src": ["...", ...]  // list of .txt or .list files
            }, ...]
        }
        """
        def get_config_file(config, base_dir=None):
            """Calculate the path of a config file.

            1. Use it if it's an absolute path.
            2. Assume relative to base_dir or CWD.
            3. Assume relative to default config directory. (.json omissible)
            4. If not found, assume relative to CWD.
            """
            if os.path.isabs(config):
                return config

            relative_config = os.path.join(base_dir, config) if base_dir is not None else config
            if os.path.isfile(relative_config):
                return relative_config

            search_file = os.path.join(self.DEFAULT_CONFIG_DIR, config)
            if os.path.isfile(search_file):
                return search_file
            if not config.lower().endswith('.json'):
                for file in glob.iglob(glob.escape(search_file) + '.[jJ][sS][oO][nN]'):
                    return file

            return relative_config

        def get_stsdict_file(stsdict):
            """Calculate the path of a dictionary file.

            1. Use it if it's an absolute path.
            2. Assume relative to the config file.
            3. Assume relative to default dictionary directory.
            4. If not found, assume relative to the config file.
            """
            if os.path.isabs(stsdict):
                return stsdict

            search_file = os.path.join(config_dir, stsdict)
            if os.path.isfile(search_file):
                return search_file

            search_file2 = os.path.join(self.DEFAULT_DICTIONARY_DIR, stsdict)
            if os.path.isfile(search_file2):
                return search_file2

            return search_file

        def check_update(output, filegroups):
            if not os.path.isfile(output):
                return True

            for files in filegroups:
                if isinstance(files, str):
                    files = [files]
                for file in files:
                    if os.path.getmtime(file) > os.path.getmtime(output):
                        return True

            return False

        # locate and load the config file
        config_file = get_config_file(config_name, base_dir)
        config_dir = os.path.abspath(os.path.dirname(config_file))

        with open(config_file, "r", encoding="UTF-8") as f:
            config = json.load(f)
            f.close()

        # handle required configs
        if not skip_requires:
            for cf in config.get('requires', []):
                self.make(cf, base_dir=config_dir, output_dir=output_dir, skip_requires=skip_requires, quiet=quiet)

        # make the requested dicts
        for dict_ in config['dicts']:
            dest = os.path.join(output_dir or config_dir, dict_['file'])
            format = dict_['format']
            mode = dict_['mode']
            files = [get_stsdict_file(f) if isinstance(f, str)
                else [get_stsdict_file(i) for i in f]
                for f in dict_['src']]

            if not check_update(dest, files):
                if not quiet: print(f'skip making (up-to-date): {dest}')
                continue

            if not quiet: print(f'making: {dest}')

            if mode == 'load':
                table = Table().load(*files)
            elif mode == 'swap':
                table = Table().load(*files).swap()
            elif mode == 'join':
                table = Table().load_filegroups(files)
            else:
                raise ValueError(f'Specified mode "{mode}" is not supported.')

            os.makedirs(os.path.dirname(dest), exist_ok=True)

            if format == 'list':
                table.dump(dest)
            elif format == 'jlist':
                table.dumpjson(dest)
            elif format == 'tlist':
                Trie().add_dict(table).dumpjson(dest)
            else:
                raise ValueError(f'Specified format "{format}" is not supported.')

        return dest

    DEFAULT_CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'data', 'config')
    DEFAULT_DICTIONARY_DIR = os.path.join(os.path.dirname(__file__), 'data', 'dictionary')

class StsConverter():
    """Convert a text using a listfile.
    """
    def __init__(self, listfile, options={}):
        _, ext = os.path.splitext(listfile)
        if ext.lower() == '.jlist':
            self.table = Table().loadjson(listfile)
        elif ext.lower() == '.tlist':
            self.table = Trie().loadjson(listfile)
        else: # default: list
            self.table = Table().load(listfile)
        self.options = {**self.default_options, **options}

    def convert(self, text):
        """Convert a text.

        Returns:
            a generator of converted data.
        """
        try:
            regex = re.compile(self.options['exclude'])
        except TypeError:
            conversion = self.table.apply(text)
        except re.error as ex:
            raise ValueError(f'regex syntax error for --exclude: {ex}')
        else:
            def convert_with_regex(text, regex):
                index = 0
                for m in regex.finditer(text):
                    start, end = m.start(0), m.end(0)

                    t = text[index:start]
                    if t:
                        yield from self.table.apply(t)

                    t = text[start:end]
                    if t:
                        try:
                            yield m.group('return')
                        except IndexError:
                            yield t

                    index = end

                t = text[index:]
                if t:
                    yield from self.table.apply(t)

            conversion = convert_with_regex(text, regex)

        yield from conversion

    def convert_text(self, text):
        """Convert a text.

        Returns:
            converted text content.
        """
        def parts_to_text(parts):
            for part in parts:
                if isinstance(part, str):
                    yield part
                else:
                    yield part[1][0]

        def parts_to_marked_text(parts):
            for part in parts:
                if isinstance(part, str):
                    yield part
                else:
                    olds, news = part
                    old = ''.join(olds)

                    if len(news) == 1 and old == news[0]:
                        yield "{{" + old + "}}"
                    else:
                        yield "{{" + old + "->" + "|".join(news) + "}}"

        def parts_to_html(parts):
            for part in parts:
                if isinstance(part, str):
                    yield html.escape(part)
                else:
                    olds, news = part
                    old = ''.join(olds)
                    content = f'<del>{html.escape(old)}</del>'
                    for i, v in enumerate(news):
                        content += f'<ins>{html.escape(v)}</ins>'

                    # classes
                    classes = ['sts-conv']
                    if len(news) == 1:
                        classes.append('single')
                    else:
                        classes.append('plural')
                    if old == news[0]:
                        classes.append('exact')
                    if len(olds) == 1:
                        classes.append('atomic')

                    part = f'''<span class="{' '.join(classes)}">{content}</span>'''
                    yield part

        conversion = self.convert(text)

        if self.options['format'] == 'htmlpage':
            return '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
pre { white-space: pre-wrap; }
span { font-weight: normal; border: thin dotted #AAA; }
span.plural { background: #FFFF99; }
span.exact { background: #DDDDFF; }
span.single { background: #CCFFCC; }
ins, del { text-decoration: none; }
</style>
</head>
<body>
<pre contenteditable="true">''' + ''.join(parts_to_html(conversion)) + '''</pre>
</body>
</html>'''
        elif self.options['format'] == 'html':
            return ''.join(parts_to_html(conversion))
        elif self.options['format'] == 'json':
            return json.dumps(list(conversion), ensure_ascii=False)
        elif self.options['format'] == 'txtm':
            return ''.join(parts_to_marked_text(conversion))
        else:  # default: format = 'txt'
            return ''.join(parts_to_text(conversion))

    def convert_file(self, input=None, output=None, input_encoding='UTF-8', output_encoding='UTF-8'):
        """Convert input and write to output.

        Args:
            input: a file path or None for stdin.
            output: a file path or None for stdout.
        """
        f = open(input, "r", encoding=input_encoding, newline="") if input else sys.stdin
        text = f.read()
        f.close()

        conversion = self.convert_text(text)

        f = open(output, "w", encoding=output_encoding, newline="") if output else sys.stdout
        f.write(conversion)
        if f is not sys.stdout: f.close()

    default_options={
        'format': 'txt',
        'exclude': None,
        }

def main():
    def sort(args):
        """Sort a conversion list.
        """
        inputs = args['file']
        outputs = args['output']

        for i, input in enumerate(inputs):
            output = input if i >= len(outputs) else outputs[i]
            Table().load(input).dump(output, sort=True)

    def swap(args):
        """Swap the key and value of a conversion list.
        """
        inputs = args['file']
        outputs = args['output']

        for i, input in enumerate(inputs):
            output = input if i >= len(outputs) else outputs[i]
            Table().load(input).swap().dump(output, sort=True)

    def merge(args):
        """Merge conversion lists.
        """
        input = args['input']
        output = args['output']

        Table().load(*input).dump(output, sort=True)

    def find(args):
        """Find the keyword in a conversion list.
        """
        keyword = args['keyword']
        input = args['input']

        for key, values in Table().load(input).find(keyword):
            print(f'{key} => {" ".join(values)}')

    def make(args):
        """Generate conversion dictionary(s).
        """
        configs = args['config']
        dir = args['dir']
        quiet = args['quiet']

        for config in configs:
            StsListMaker().make(config, output_dir=dir, quiet=quiet)

    def convert(args):
        """Convert a file using the given config.
        """
        inputs = args['file']
        outputs = args['output']
        force_stdout = args['stdout']
        config = args['config']
        options={
            'format': args['format'],
            'exclude': args['exclude'],
            }
        input_encoding = args['in_enc']
        output_encoding = args['out_enc']

        stsdict = StsListMaker().make(config, quiet=True)
        converter = StsConverter(stsdict, options)

        # read STDIN if no input file is specified
        if not len(inputs):
            inputs.append(None)

        for i, input in enumerate(inputs):
            output = None if force_stdout else input if i >= len(outputs) else outputs[i]
            converter.convert_file(input, output, input_encoding, output_encoding)

    # define the parsers
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default=False, action='store_true',
        help="""show version information and exit""")
    subparsers = parser.add_subparsers(dest='func', metavar='COMMAND')

    # subcommand: convert
    parser_convert = subparsers.add_parser('convert',
        help=convert.__doc__, description=convert.__doc__)
    parser_convert.add_argument('file', nargs='*',
        help="""file(s) to convert (default: STDIN)""")
    parser_convert.add_argument('--config', '-c', default='s2t',
        help="""the config to use, either a built-in config name or a path to a custom JSON file
(built-in configs: s2t|t2s|s2tw|tw2s|s2twp|tw2sp|s2hk|hk2s|t2tw|tw2t|t2twp|tw2tp|t2hk|hk2t|t2jp|jp2t)
(default: %(default)s)""")
    parser_convert.add_argument('--format', '-f', default="txt",
        choices=['txt', 'txtm', 'html', 'htmlpage', 'json'], metavar='FORMAT',
        help="""output format (txt|txtm|html|htmlpage|json) (default: %(default)s)""")
    parser_convert.add_argument('--exclude',
        help="""exclude text matching given regex from conversion, and replace it with the "return" subgroup value if exists""")
    parser_convert.add_argument('--in-enc', default='UTF-8', metavar='ENCODING',
        help="""encoding for input (default: %(default)s)""")
    parser_convert.add_argument('--out-enc', default='UTF-8', metavar='ENCODING',
        help="""encoding for output (default: %(default)s)""")
    parser_convert.add_argument('--output', '-o', default=[], action='append',
        help="""path to output (for the corresponding input) (default: to input)""")
    parser_convert.add_argument('--stdout', default=False, action='store_true',
        help="""write all converted text to STDOUT instead""")

    # subcommand: sort
    parser_sort = subparsers.add_parser('sort',
        help=sort.__doc__, description=sort.__doc__)
    parser_sort.add_argument('file', nargs='+',
        help="""file(s) to sort""")
    parser_sort.add_argument('--output', '-o', default=[], action='append',
        help="""path to output (for the corresponding input) (default: to input)""")

    # subcommand: swap
    parser_swap = subparsers.add_parser('swap',
        help=swap.__doc__, description=swap.__doc__)
    parser_swap.add_argument('file', nargs='+',
        help="""file(s) to swap""")
    parser_swap.add_argument('--output', '-o', default=[], action='append',
        help="""path to output (for the corresponding input) (default: to input)""")

    # subcommand: merge
    parser_merge = subparsers.add_parser('merge',
        help=merge.__doc__, description=merge.__doc__)
    parser_merge.add_argument('input', nargs='+',
        help="""files to merge""")
    parser_merge.add_argument('output',
        help="""file to save as""")

    # subcommand: find
    parser_find = subparsers.add_parser('find',
        help=find.__doc__, description=find.__doc__)
    parser_find.add_argument('keyword',
        help="""keyword to find""")
    parser_find.add_argument('input',
        help="""file to find""")

    # subcommand: make
    parser_make = subparsers.add_parser('make',
        help=make.__doc__, description=make.__doc__)
    parser_make.add_argument('config', nargs='+',
        help="""the config(s) to generate""")
    parser_make.add_argument('--dir', '-d', default=None,
        help="""the directory to save the output (default: relative to config)""")
    parser_make.add_argument('--quiet', '-q', default=False, action='store_true',
        help="""do not show process information""")

    # parse the command
    args = vars(parser.parse_args())
    if args['func']:
        locals()[args['func']](args)
    elif args['version']:
        print(f'sts {__version__}')
    else:
        parser.parse_args(['-h'])

if __name__ == "__main__":
    main()
