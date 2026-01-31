#!/usr/bin/env python3
"""An open library for flexible simplified-traditional Chinese text conversion."""
__version__ = '0.37.1'

import html
import itertools
import json
import math
import os
import re
import sys
from collections import namedtuple
from contextlib import nullcontext
from functools import cached_property

StsDictMatch = namedtuple('StsDictMatch', ['conv', 'start', 'end'])
StsDictConv = namedtuple('StsDictConv', ['key', 'values'])
StsConvExclude = namedtuple('StsConvExclude', ['text'])


def file_input(file, encoding='UTF-8-SIG', newline=None):
    try:
        return open(file, 'r', encoding=encoding, newline=newline)
    except TypeError:
        return nullcontext(sys.stdin if file is None else file)


def file_output(file, encoding='UTF-8', newline=''):
    try:
        return open(file, 'w', encoding=encoding, newline=newline)
    except TypeError:
        return nullcontext(sys.stdout if file is None else file)


class StreamList(list):
    """Convert an iterable into a serializable "list".

    This turns an iterable into an iterator that can be serialized as a JSON
    Array incrementally (i.e. without read into the memory as a whole).

    - Must be an instance of list (to make JSON encoder treat as a list).
    - Must be truthy if and only if non-empty.
    """
    def __init__(self, iterable):
        self._iterator = iter(iterable)
        self._head_sent = False

    def __iter__(self):
        return self

    def __next__(self):
        if self._head_sent:
            return next(self._iterator)
        if not hasattr(self, '_head'):
            self._head = next(self._iterator)
        self._head_sent = True
        return self._head

    def __bool__(self):
        if hasattr(self, '_head'):
            return True
        try:
            self._head = next(self._iterator)
        except StopIteration:
            return False
        else:
            return True


class Unicode():
    """Utilities for Unicode string handling.

    We also allow IVI and VS in an IDS.
    """
    @classmethod
    def is_valid_ids_hanzi(cls, code):
        """Test if code is a valid "hanzi" in an IDS.

        IDS := Ideographic | Radical | CJK_Stroke | Private Use
             | U+FF1F
             | IDS_UnaryOperator IDS
             | IDS_BinaryOperator IDS IDS
             | IDS_TrinaryOperator IDS IDS IDS
        """
        return (
            0x4E00 <= code <= 0x9FFF  # CJK unified
            or 0x3400 <= code <= 0x4DBF  # Ext-A
            or 0xF900 <= code <= 0xFAFF  # CJK Compatibility Ideographs
            or 0x20000 <= code <= 0x3FFFF  # ExtB+ (including CJK Compatibility Ideographs Supplement)
            or 0x2E80 <= code <= 0x2FDF  # Radical
            or 0x31C0 <= code <= 0x31EF  # Stroke
            or 0xE000 <= code <= 0xF8FF or 0xF0000 <= code <= 0x1FFFFF  # Private
            or code == 0xFF1F  # ？
            or 0xFE00 <= code <= 0xFE0F or 0xE0100 <= code <= 0xE01EF  # VS (non-standard)
        )

    @classmethod
    def is_hanzi(cls, code):
        """Test if code is a "hanzi" (which prefers no space)."""
        return (
            cls.is_valid_ids_hanzi(code)
            or 0x2FF0 <= code <= 0x33FF  # IDS operator
                                         # CJK Symbols and Punctuation (including IVI)
                                         # Hiragana
                                         # Katakana
                                         # Bopomofo
                                         # Hangul Compatibility Jamo
                                         # Kanbun
                                         # Bopomofo Extended
                                         # (CJK Strokes)
                                         # Katakana Phonetic Extensions
                                         # Enclosed CJK Letters and Months
                                         # CJK Compatibility
            or 0xFF00 <= code <= 0xFFEF  # Halfwidth and Fullwidth Forms
        )

    @classmethod
    def composite_length(cls, text, pos):
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
            elif 0x2FFE <= code <= 0x2FFF:
                # IDS unary operator
                is_ids = True
                length += 1
            elif 0x2FF0 <= code <= 0x2FF1 or 0x2FF4 <= code <= 0x2FFD or code == 0x31EF:
                # IDS binary operator
                is_ids = True
                length += 2
            elif 0x2FF2 <= code <= 0x2FF3:
                # IDS trinary operator
                is_ids = True
                length += 3
            elif is_ids and not cls.is_valid_ids_hanzi(code):
                # check for a valid IDS to avoid a breaking on e.g.:
                #
                #     IDS包括⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻，可用於…
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

    @classmethod
    def split(cls, text):
        """Split a text into a list of Unicode composites."""
        i = 0
        total = len(text)
        result = []
        while i < total:
            length = cls.composite_length(text, i)
            result.append(text[i:i + length])
            i += length
        return result


class StsDict():
    """Base class of an STS dictionary.

    This class is for child classes to implement on and not intended to be
    used directly.

    Supported serializations are:
    - plain-dict: which is a text file that looks like:

          key1 <tab> value1-1 [<space> value1-2 <space> ...]
          key2 <tab> value2-1 [<space> value2-2 <space> ...]
          ...

    - JSON: which is dumped from the internal data structure.
    """
    def __init__(self, *args, **kwargs):
        self._dict = {}
        self.update(dict(*args, **kwargs))

    def __repr__(self):
        """Implementation of repr(self)."""
        return f'{self.__class__.__name__}({repr(list(self.items()))})'

    def __getitem__(self, key):
        """Implementation of self[key]."""
        return self._dict[key]

    def __contains__(self, item):
        """Implementation of "item in self"."""
        return item in self._dict

    def __len__(self):
        """Implementation of len(self)."""
        return len(self._dict)

    def __iter__(self):
        """Implementation of iter(self)."""
        return iter(self._dict)

    def __eq__(self, other):
        """Implementation of "==" operator."""
        if not isinstance(other, (dict, StsDict)):
            return False

        # faster check for the same type
        if type(self) is type(other):
            return self._dict == other._dict

        keys = set()
        for key, value in self.items():
            try:
                assert value == other[key]
            except (KeyError, AssertionError):
                return False
            keys.add(key)
        for key in other:
            if key not in keys:
                return False
        return True

    def __delitem__(self, key):
        """Implementation of del self[key]."""
        del self._dict[key]

    def keys(self):
        """Generate keys."""
        yield from self._dict.keys()

    def values(self):
        """Generate values."""
        yield from self._dict.values()

    def items(self):
        """Generate key-values pairs."""
        yield from self._dict.items()

    def add(self, key, values, skip_check=False):
        """Add a key-values pair to this dictionary.

        Args:
            values: a string or an iterable of strings.
            skip_check: True to skip checking duplicated values.
        """
        values = (values,) if isinstance(values, str) else values
        list_ = self._dict.setdefault(key, [])
        list_ += values if skip_check else (x for x in values if x not in list_)
        return self

    def update(self, stsdict, skip_check=False):
        """Add all key-values pairs from another StsDict or dict.

        Args:
            skip_check: True to skip checking duplicated values.
        """
        for key, values in stsdict.items():
            self.add(key, values, skip_check=skip_check)
        return self

    def load(self, file, type=None):
        """Add all key-values pairs from a dict file."""
        if type is None and isinstance(file, str):
            t = os.path.splitext(file)[1][1:].lower()
        else:
            t = type
        if t in ('json', 'jlist'):
            self._load_json(file)
        elif t in ('yaml', 'yml'):
            self._load_yaml(file)
        else:
            self._load_plain(file)
        return self

    def _load_plain(self, file):
        with file_input(file) as fh:
            for line in fh:
                line = line.rstrip('\n')

                # skip comment (OpenCC >= 1.2.0) or empty line
                if not line or line.startswith('#'):
                    continue

                try:
                    key, values, *_ = line.split('\t')
                except ValueError:
                    # no '\t', treat as key => [key]
                    self.add(line, line)
                else:
                    self.add(key, values.split(' '))

    def _load_json(self, file):
        with file_input(file) as fh:
            data = json.load(fh)
            if not isinstance(data, dict):
                data = dict(data)
            self.update(data)

    def _load_yaml(self, file):
        try:
            import yaml
        except ModuleNotFoundError:
            raise RuntimeError('install PyYAML module to support loading .yaml files')

        with file_input(file) as fh:
            data = yaml.safe_load(fh)
            if not isinstance(data, dict):
                data = dict(data)
            self.update(data)

    def dump(self, file=None, sort=False, check=False):
        """Dump key-values pairs to a plain-dict file.

        Args:
            file: file to save as a path-like, file-like, or None for stdout.
            sort: True to sort the output.
        """
        it = self.items()
        if sort:
            it = sorted(it)
        with file_output(file) as fh:
            for key, values in it:
                if check:
                    for badchar in '\t\n\r':
                        if badchar in key:
                            raise ValueError(
                                f'{repr(key)} => {repr(values)} contains invalid {repr(badchar)}'
                            )
                    for badchar in ' \t\n\r':
                        if any(badchar in v for v in values):
                            raise ValueError(
                                f'{repr(key)} => {repr(values)} contains invalid {repr(badchar)}'
                            )
                fh.write(f'{key}\t{" ".join(values)}\n')

    @classmethod
    def loadjson(cls, file):
        """Load from a JSON file.

        NOTE: The input data format may vary across subclasses.

        Args:
            file: file to load as a path-like, file-like, or None for stdin.

        Returns:
            a new object with the same class.
        """
        with file_input(file) as fh:
            stsdict = cls()
            stsdict._dict = json.load(fh)
        return stsdict

    def dumpjson(self, file=None, indent=None, sort=False):
        """Dump key-values pairs to a JSON file.

        NOTE: The output data format may vary across subclasses.

        Args:
            file: file to save as a path-like, file-like, or None for stdout.
            indent: indent the output with a specified integer.
            sort: True to sort the output.
        """
        with file_output(file) as fh:
            json.dump(
                self._dict, fh, indent=indent, sort_keys=sort,
                separators=(',', ':') if indent is None else None,
                ensure_ascii=False, check_circular=False,
            )

    def print(self, sort=False):
        """Print key-values pairs.

        Args:
            sort: True to sort the output.
        """
        it = self.items()
        if sort:
            it = sorted(it)
        for key, values in it:
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
        for key, values in self.items():
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
        for key, values in self.items():
            for value in values:
                stsdict.add(value, key)
        return stsdict

    def join(self, stsdict):
        """Join another dictionary.

        Applying the returned dictionary to a text simulates the effect
        of applying using self and then using stsdict.

        This will invoke stsdict.apply_enum and it's recommended that stsdict
        be a Table or Trie for better performance.

        Returns:
            a new object with the same class.
        """
        newdict = self.__class__()

        """postfix

        Convert values of self using stsdict, enumerating all longest
        conversions.

        Example:
            self:
                因为 => 因爲
            stsdict:
                爲 => 為
            result:
                因为 => 因為
        """
        for key, values in self.items():
            for value in values:
                newdict.add(key, stsdict.apply_enum(value))

        """prefix

        Add every string that may become a stsdict key after converted by self
        as a new key.

        Example:
            self:
                纳 => 納
            stsdict:
                納米 => 奈米
            result:
                纳米 => 奈米

        Example:
            self:
                妳 => 你 奶
            stsdict:
                奶娘 => 奶媽
            result:
                妳娘 => 你娘 奶媽

        Example:
            self:
                妳 => 你 奶
            stsdict:
                奶娘 => 奶媽
                你娘 => 妳媽
            result:
                妳娘 => 妳媽 奶媽
        """
        conv = self.swap()

        map_keys = {}
        for key in stsdict:
            for newkey in conv.apply_enum(key, include_short=True, include_self=True):
                map_keys.setdefault(newkey, None)

        for key in map_keys:
            newkeys = self.apply_enum(key)
            for newkey in newkeys:
                try:
                    assert stsdict[newkey]
                except (KeyError, AssertionError):
                    pass
                else:
                    break
            else:
                continue

            for newkey in newkeys:
                values = stsdict.apply_enum(newkey)
                newdict.add(key, values)

        return newdict

    def _split(self, text):
        """Split text into a list of Unicode composites.

        With automatic type handling.
        """
        if isinstance(text, str):
            return Unicode.split(text)
        elif isinstance(text, list):
            return text
        else:
            return list(text)

    def match(self, text, pos, maxpos=math.inf):
        """Match a unicode composite at pos.

        Args:
            text: a string or iterable parts to be matched.

        Returns:
            an StsDictMatch or None if no match.
        """
        return self._match(self._split(text), pos, maxpos)

    def _match(self, parts, pos, maxpos=math.inf):
        try:
            i = max(len(Unicode.split(key)) for key in self._dict)
        except ValueError:
            # self._dict is empty
            i = 0
        i = min(i, min(len(parts), maxpos) - pos)
        while i >= 1:
            end = pos + i
            current_parts = parts[pos:end]
            current = ''.join(current_parts)
            try:
                match = self._dict[current]
                assert match
            except (KeyError, AssertionError):
                pass
            else:
                conv = StsDictConv(current_parts, match)
                return StsDictMatch(conv, pos, end)
            i -= 1
        return None

    def apply(self, text):
        """Convert text using the dictionary.

        Args:
            text: a string or iterable parts to be converted.

        Yields:
            the next converted part as an StsDictConv, or an unmatched part as
            a str.
        """
        return self._apply(self._split(text))

    def _apply(self, parts):
        i = 0
        total = len(parts)
        while i < total:
            match = self._match(parts, i)
            if match is not None:
                yield match.conv
                i = match.end
            else:
                yield parts[i]
                i += 1

    def apply_enum(self, text, include_short=False, include_self=False):
        """Enumerate all possible conversions of text.

        Example:
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

        Args:
            text: a string or iterable parts to be converted.
            include_short: include non-maximal-match conversions
            include_self: include source for every match

        Returns:
            a list of possible conversions.
        """
        parts = self._split(text)
        total = len(parts)
        stack = [((), 0, 0)]
        substack = []
        results = {}
        while stack:
            subparts, index, matched = ctx = stack.pop()
            if index < total:
                self._apply_enum_sub(parts, ctx, substack, include_short, include_self)
                while substack:
                    stack.append(substack.pop())
            elif matched > 0:
                results[''.join(subparts)] = None

        results = list(results)

        if not results:
            results.append(text if isinstance(text, str) else ''.join(text))

        return results

    def _apply_enum_sub(self, parts, ctx, stack, include_short, include_self):
        subparts, index, matched = ctx
        has_atomic_match = False
        i = math.inf
        while i > index:
            match = self._match(parts, index, i)

            if match is None:
                break

            if match.end - index == 1:
                has_atomic_match = True

            values = match.conv.values
            if include_self:
                key = ''.join(match.conv.key)
                if key not in values:
                    values = itertools.chain(values, (key,))

            for value in values:
                stack.append((subparts + (value,), match.end, matched + 1))

            if not include_short:
                return

            i = match.end - 1

        """Add an atomic stepping (index + 1) case if not presented.

        Example:
            table:
                信息 => 訊息
            parts:
                ['采', '信', '息']
            ctx:
                ((), 0, 0)

            We get no match, which implies no atomic match (i.e. '采'). Add
            ctx=(('采',), 1, 0) so that the possible conversion ['采', '訊息']
            is not missing.

        Example:
            table:
                采信 => 採信
                信息 => 訊息
            parts:
                ['采', '信', '息']
            ctx:
                ((), 0, 0)

            We get a match '采信' but no atomic match (i.e. '采'). Add
            ctx=(('采',), 1, 0) so that the possible conversion ['采', '訊息']
            is not missing.
        """
        if not has_atomic_match:
            stack.append((subparts + (parts[index],), index + 1, matched))


class Table(StsDict):
    """A cache-boosted STS dictionary.

    This class implements a cache and a head-char checking mechanism to
    improve performance on text conversion than base StsDict.

    The internal data format is same as base StsDict.
    """
    key_head_length = 2

    @cached_property
    def head_map(self):
        """Get a dict of the first N parts to max length."""
        dict_ = {}
        for key in self._dict:
            parts = Unicode.split(key)
            length = len(parts)
            if length < self.key_head_length:
                continue
            head = ''.join(parts[:self.key_head_length])
            dict_[head] = max(dict_.get(head, 0), length)
        return dict_

    def add(self, key, values, skip_check=False):
        try:
            del self.head_map
        except AttributeError:
            pass
        return super().add(key, values, skip_check)

    def update(self, stsdict, skip_check=False):
        try:
            del self.head_map
        except AttributeError:
            pass
        fn = super().add
        for key, values in stsdict.items():
            fn(key, values, skip_check)
        return self

    def _match(self, parts, pos, maxpos=math.inf):
        try:
            i = self.head_map[''.join(parts[pos:pos + self.key_head_length])]
        except KeyError:
            i = self.key_head_length - 1
        i = min(i, min(len(parts), maxpos) - pos)
        while i >= 1:
            end = pos + i
            current_parts = parts[pos:end]
            current = ''.join(current_parts)
            try:
                match = self._dict[current]
                assert match
            except (KeyError, AssertionError):
                pass
            else:
                conv = StsDictConv(current_parts, match)
                return StsDictMatch(conv, pos, end)
            i -= 1
        return None


class Trie(StsDict):
    """An STS dictionary with trie (prefix tree) format.

    Compared with hash, trie is faster for applying conversion,
    but takes more space and is slower to construct.

    NOTE: The internal data format is different from base StsDict.
    """
    def __getitem__(self, key):
        """Implementation of self[key]."""
        trie = self._dict
        try:
            for char in key:
                trie = trie[char]
            return trie['']
        except KeyError:
            raise KeyError(key)

    def __contains__(self, item):
        """Implementation of "item in self"."""
        try:
            self[item]
        except KeyError:
            return False
        else:
            return True

    def __len__(self):
        """Implementation of len(self)."""
        return sum(1 for _ in self)

    def __iter__(self):
        """Implementation of iter(self)."""
        return self.keys()

    def __delitem__(self, key):
        """Implementation of del self[key]."""
        trie = self._dict
        try:
            for char in key:
                trie = trie[char]
            del trie['']
        except KeyError:
            raise KeyError(key)

    def keys(self):
        """Generate keys."""
        trie = self._dict
        stack = [('', trie)]
        while stack:
            key, trie = stack.pop()
            for char in reversed(trie):
                if char == '':
                    yield key
                else:
                    stack.append((key + char, trie[char]))

    def values(self):
        """Generate values."""
        trie = self._dict
        stack = [trie]
        while stack:
            trie = stack.pop()
            for char in reversed(trie):
                if char == '':
                    yield trie[char]
                else:
                    stack.append(trie[char])

    def items(self):
        """Generate key-values pairs."""
        trie = self._dict
        stack = [('', trie)]
        while stack:
            key, trie = stack.pop()
            for char in reversed(trie):
                if char == '':
                    yield key, trie[char]
                else:
                    stack.append((key + char, trie[char]))

    def add(self, key, values, skip_check=False):
        """Add a key-values pair to this dictionary.

        Args:
            values: a string or a list of strings.
            skip_check: True to skip checking duplicated values.
        """
        values = (values,) if isinstance(values, str) else values

        trie = self._dict
        for char in key:
            trie = trie.setdefault(char, {})

        list_ = trie.setdefault('', [])
        list_ += values if skip_check else (x for x in values if x not in list_)
        return self

    def _match(self, parts, pos, maxpos=math.inf):
        trie = self._dict
        i = pos
        end = min(len(parts), maxpos)
        match = None
        match_end = None
        while i < end:
            try:
                for char in parts[i]:
                    trie = trie[char]
            except KeyError:
                break
            try:
                values = trie['']
                assert values
            except (KeyError, AssertionError):
                pass
            else:
                match = values
                match_end = i + 1
            i = i + 1
        if match:
            conv = StsDictConv(parts[pos:match_end], match)
            return StsDictMatch(conv, pos, match_end)
        return None


class StsMaker():
    """A class for making dictionary file(s)."""
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    config_dir = os.path.join(data_dir, 'config')
    dictionary_dir = os.path.join(data_dir, 'dictionary')

    def make(self, config_name, base_dir=None,
             skip_check=False, skip_requires=False, quiet=False):
        """Make dictionary file(s) according to a config.

        scheme of config (.json):
            {
                "name": "...",
                "requires": [
                    "..."  // a required config (relative to this config file)
                ],
                "dicts": [  // dictionaries to generate
                    {
                        "file": "...",  // path of the generated dictionary
                                        // file, relative to config dir
                        "mode": "...",  // mode to handle the loaded sources:
                                        // load, swap, join
                        "src": [        // list of the source file paths,
                            src1,       // should be .txt or .list files
                            src2,
                            ...
                        ],
                        "sort": true,   // truthy to sort the keys of the
                                        // generated dictionary
                        "check": true,  // check for invalid output
                    },
                    ...
                ]
            }

        Args:
            config_name: a str for the config file or name
            base_dir: a str for the base directory to parse the config path
                from config_name, or None for CWD
            skip_check: truthy to generate every dictionary no matter that it's
                already up-to-date
            skip_requires: truthy to skip making from required configs
            quiet: truthy to skip reporting details

        Returns:
            a str for the path of the last generated dictionary file or None
        """
        # locate and load the config file
        config_file = self.get_config_file(config_name, base_dir=base_dir)
        config_dir = os.path.abspath(os.path.dirname(config_file))
        try:
            config = self.load_config(config_file)
        except Exception as exc:
            raise RuntimeError(f'failed to load config file "{config_file}": {exc}')
        self.normalize_config(config, config_dir)

        # handle required configs
        if not skip_requires:
            for cf in config['requires']:
                self.make(cf, base_dir=config_dir, skip_requires=skip_requires, quiet=quiet)

        # make the requested dicts
        dest = None
        for dict_scheme in config['dicts']:
            if isinstance(dict_scheme, str):
                dest = dict_scheme
                if not os.path.isfile(dest):
                    raise RuntimeError(f'specified dict file does not exist: {dest}')
                continue

            dest = dict_scheme['file']

            if dest is None:
                raise RuntimeError('dict["file"] is not specified')

            if not skip_check and not self.check_update(dict_scheme):
                if not quiet:
                    print(f'skip making (up-to-date): {dest}')
                continue

            self.make_dict(dict_scheme, config_dir=config_dir, skip_check=skip_check, quiet=quiet)

        return dest

    def load_config(self, config_file):
        ext = os.path.splitext(config_file)[1][1:].lower()

        if ext in ('yaml', 'yml'):
            try:
                import yaml
            except ModuleNotFoundError:
                raise RuntimeError('install PyYAML module to support loading .yaml config')

            with open(config_file, 'r', encoding='UTF-8') as fh:
                config = yaml.safe_load(fh)

        else:  # default: json
            with open(config_file, 'r', encoding='UTF-8') as fh:
                config = json.load(fh)

        return config

    def normalize_config(self, config, config_dir):
        """Normalize and validate config in place."""
        if not isinstance(config, dict):
            raise ValueError('config is not a dict')

        config.setdefault('requires', [])

        try:
            dict_schemes = config['dicts']
        except KeyError:
            raise ValueError('config["dicts"] is not specified')

        for i, dict_scheme in enumerate(dict_schemes):
            dict_schemes[i] = self.normalize_dict_scheme(dict_scheme, config_dir)

        return config

    def normalize_dict_scheme(self, dict_scheme, config_dir):
        """Recursively normalize and validiate dict_scheme in place.

        - Resolve file paths.

        Args:
            dict_scheme: a dict or a str for the dictionary path
        """
        if isinstance(dict_scheme, str):
            return self.get_stsdict_file(dict_scheme, config_dir)

        try:
            dict_scheme['file'] = os.path.normpath(os.path.join(config_dir, dict_scheme['file']))
        except KeyError:
            dict_scheme['file'] = None

        try:
            srcs = dict_scheme['src']
        except KeyError:
            dict_scheme['src'] = []
        else:
            for i, src in enumerate(srcs):
                srcs[i] = self.normalize_dict_scheme(src, config_dir)

        mode = dict_scheme.setdefault('mode', 'load')
        dict_scheme['sort'] = bool(dict_scheme.get('sort'))
        dict_scheme['check'] = bool(dict_scheme.get('check'))
        dict_scheme['auto_space'] = bool(dict_scheme.get('auto_space'))

        if mode == 'filter':
            method = dict_scheme.setdefault('method', 'remove_key_values')
            if method not in ('remove_keys', 'remove_key_values'):
                raise ValueError(f'unknown method for filter: {method}')

            try:
                dict_scheme['include'] = re.compile(dict_scheme['include'])
            except KeyError:
                dict_scheme['include'] = None
            except re.error as exc:
                raise ValueError(f'regex syntax error of the "include" filter: {exc}')

            try:
                dict_scheme['exclude'] = re.compile(dict_scheme['exclude'])
            except KeyError:
                dict_scheme['exclude'] = None
            except re.error as exc:
                raise ValueError(f'regex syntax error of the "exclude" filter: {exc}')

        elif mode == 'expand':
            dict_scheme.setdefault('placeholders', [])
            if len(dict_scheme['placeholders']) != len(srcs) - 1:
                raise ValueError('len(dict["placeholders"]) must be len(dict["src"]) - 1')

        return dict_scheme

    def make_dict(self, dict_scheme, config_dir, skip_check=False, quiet=False):
        """Make a dict.

        Returns:
            A StsDict or str (for str scheme or when up-to-date).
        """
        if isinstance(dict_scheme, str):
            return dict_scheme

        dest = dict_scheme.get('file')
        if dest:
            if not skip_check and not dict_scheme.get('_updated'):
                return dest

            format = os.path.splitext(dest)[1][1:].lower()
        else:
            format = '.list'

        mode = dict_scheme['mode']
        srcs = dict_scheme['src']
        sort = dict_scheme['sort']

        if not srcs:
            if not os.path.isfile(dest):
                raise RuntimeError(f'Specified flie does not exist: {dest}')
            return dest

        if dest and not quiet:
            print(f'making: {dest}')

        for i, src in enumerate(srcs):
            srcs[i] = self.make_dict(src, config_dir, skip_check, quiet)

        try:
            func = getattr(self, f'_make_dict_mode_{mode}')
        except AttributeError:
            raise ValueError(f'Specified mode is not supported: {mode}')
        else:
            table = func(dict_scheme)

        if dict_scheme['auto_space']:
            self._make_dict_auto_space(table)

        if dest:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if format == 'tlist':
                Trie(table).dumpjson(dest, sort=sort)
            elif format == 'jlist':
                table.dumpjson(dest, sort=sort)
            else:  # default: list
                table.dump(dest, sort=sort, check=dict_scheme['check'])

        return table

    def _make_dict_mode_load(self, dict_scheme):
        table = Table()
        for src in dict_scheme['src']:
            if isinstance(src, str):
                table.load(src)
            else:
                table.update(src)
        return table

    def _make_dict_mode_swap(self, dict_scheme):
        table = self._make_dict_mode_load(dict_scheme)
        table = table.swap()
        return table

    def _make_dict_mode_join(self, dict_scheme):
        table = Table()
        for src in dict_scheme['src']:
            dict_ = Table().load(src) if isinstance(src, str) else src
            table = table.join(dict_)
        return table

    def _make_dict_mode_expand(self, dict_scheme):
        newtable = Table()

        srcs = dict_scheme['src']
        src = srcs.pop(0)
        table = Table().load(src) if isinstance(src, str) else src
        dicts = [Table().load(src) if isinstance(src, str) else src for src in srcs]

        placeholders = dict_scheme['placeholders']
        ph_table = Trie({p: p for p in placeholders})
        map_ph_to_dict_idx = {p: i for i, p in enumerate(placeholders)}

        for key, values in table.items():
            key_parts = list(ph_table.apply(key))
            value_parts_list = [list(ph_table.apply(v)) for v in values]

            map_ph_to_comb_idx = {}
            for part in itertools.chain(key_parts, *value_parts_list):
                if isinstance(part, str):
                    continue
                ph = ''.join(part.key)
                map_ph_to_comb_idx.setdefault(ph, len(map_ph_to_comb_idx))

            # shortcut when no placeholder
            if not map_ph_to_comb_idx:
                newtable.add(key, values)
                continue

            it = (dicts[map_ph_to_dict_idx[ph]] for ph in map_ph_to_comb_idx)
            for comb in itertools.product(*it):
                context = (dicts, comb, map_ph_to_dict_idx, map_ph_to_comb_idx)
                newkey = self._make_dict_mode_expand_get_expanded_key(key_parts, context)
                newvalues = itertools.chain.from_iterable(
                    self._make_dict_mode_expand_get_expanded_values(vpp, context)
                    for vpp in value_parts_list
                )
                newtable.add(newkey, newvalues)

        return newtable

    @staticmethod
    def _make_dict_mode_expand_get_expanded_key(parts, context):
        _, comb, _, map_ph_to_comb_idx = context
        rv = []
        for part in parts:
            if isinstance(part, str):
                rv.append(part)
                continue

            ph = ''.join(part.key)
            rv.append(comb[map_ph_to_comb_idx[ph]])
        return ''.join(rv)

    @staticmethod
    def _make_dict_mode_expand_get_expanded_values(parts, context):
        dicts, comb, map_ph_to_dict_idx, map_ph_to_comb_idx = context
        rv = []
        stack = [(parts, 0)]
        while stack:
            parts, idx = stack.pop()
            try:
                part = parts[idx]
            except IndexError:
                rv.append(''.join(parts))
                continue

            if isinstance(part, str):
                stack.append((parts, idx + 1))
                continue

            ph = ''.join(part.key)
            dict_idx = map_ph_to_dict_idx[ph]
            comb_idx = map_ph_to_comb_idx[ph]
            for value in reversed(dicts[dict_idx][comb[comb_idx]]):
                newparts = parts[:idx] + [value] + parts[idx + 1:]
                stack.append((newparts, idx + 1))
        return rv

    def _make_dict_mode_filter(self, dict_scheme):
        method = getattr(self, f'_make_dict_mode_filter_method_{dict_scheme["method"]}')

        srcs = dict_scheme['src']
        src = srcs.pop(0)
        table = Table().load(src) if isinstance(src, str) else src
        for src in srcs:
            dict_ = Table().load(src) if isinstance(src, str) else src
            method(table, dict_)

        include = dict_scheme['include']
        exclude = dict_scheme['exclude']
        if include or exclude:
            _table = table
            table = Table()
            for key, values in _table.items():
                values = [v for v in values
                          if (include is None or include.search(v))
                          and (exclude is None or not exclude.search(v))]
                if values:
                    table.add(key, values)

        return table

    @staticmethod
    def _make_dict_mode_filter_method_remove_keys(table, dict):
        for k in dict:
            try:
                del table[k]
            except KeyError:
                continue

    @staticmethod
    def _make_dict_mode_filter_method_remove_key_values(table, dict):
        for k, vv in dict.items():
            try:
                t = table[k]
            except KeyError:
                continue
            for v in vv:
                try:
                    t.remove(v)
                except ValueError:
                    pass
            if not t:
                del table[k]

    def _make_dict_auto_space(self, table):
        extra_table = Table()
        for key, values in table.items():
            newkey = self._make_dict_auto_space_make_spaced(key)
            if newkey != key and newkey not in table:
                newvalues = [self._make_dict_auto_space_make_spaced(v) for v in values]
                extra_table.add(newkey, newvalues)
        for key, values in extra_table.items():
            table.add(key, values, skip_check=True)

    @staticmethod
    def _make_dict_auto_space_make_spaced(text):
        last_is_hanzi = None
        rv = []
        parts = Unicode.split(text)
        for part in parts:
            is_hanzi = all(Unicode.is_hanzi(ord(c)) for c in part)
            if last_is_hanzi is None:
                last_is_hanzi = is_hanzi
            elif last_is_hanzi != is_hanzi:
                rv.append(' ')
                last_is_hanzi = is_hanzi
            rv.append(part)
        return ''.join(rv)

    def get_config_file(self, config, base_dir=None):
        """Calculate the path of a config file.

        1. Use it if it's an absolute path.
        2. Assume relative to base_dir or CWD.
        3. Assume relative to default config directory. (basename only; .json omissible)
        4. If not found, return 2.
        """
        if os.path.isabs(config):
            return os.path.normpath(config)

        relative_config = os.path.join(base_dir, config) if base_dir is not None else config
        if os.path.isfile(relative_config):
            return os.path.normpath(relative_config)

        if os.path.basename(config) == config:
            search_file = os.path.join(self.config_dir, config)
            if os.path.isfile(search_file):
                return os.path.normpath(search_file)

            exts = ('.json', '.yaml', '.yml')
            ext = os.path.splitext(config)[1].lower()
            if ext not in exts:
                for ext in exts:
                    search_file = os.path.join(self.config_dir, config + ext)
                    if os.path.isfile(search_file):
                        return os.path.normpath(search_file)

        return os.path.normpath(relative_config)

    def get_stsdict_file(self, stsdict, base_dir=None):
        """Calculate the path of a dictionary file.

        1. Use it if it's an absolute path.
        2. Assume relative to base_dir or CWD.
        3. Assume relative to default dictionary directory. (basename only)
        4. If not found, return 2.
        """
        if os.path.isabs(stsdict):
            return os.path.normpath(stsdict)

        relative_stsdict = os.path.join(base_dir, stsdict) if base_dir is not None else stsdict
        if os.path.isfile(relative_stsdict):
            return os.path.normpath(relative_stsdict)

        if os.path.basename(stsdict) == stsdict:
            search_file = os.path.join(self.dictionary_dir, stsdict)
            if os.path.isfile(search_file):
                return os.path.normpath(search_file)

        return os.path.normpath(relative_stsdict)

    def check_update(self, dict_scheme, mtime=math.inf):
        """Recursively check if dict_scheme needs update.

        Updated dict_scheme or descendant dict_scheme sets
        dict_scheme['_updated'] = True.

        Returns:
            bool: True if needs update and False otherwise.
        """
        if isinstance(dict_scheme, str):
            dict_scheme = {'file': dict_scheme}

        rv = False

        file = dict_scheme.get('file')

        if file:
            if not os.path.isfile(file):
                rv = dict_scheme['_updated'] = True
            else:
                file_mtime = os.path.getmtime(file)
                if file_mtime > mtime:
                    rv = True

                mtime = file_mtime

        srcs = dict_scheme.get('src', ())
        for src in srcs:
            if self.check_update(src, mtime):
                rv = dict_scheme['_updated'] = True

        return rv


class StsConverter():
    """Convert a text using an stsdict."""
    exclude_return_group_pattern = re.compile(r'^return\d*$')
    template_placeholder_pattern = re.compile(r'%(\w*)%')
    htmlpage_template = os.path.join(os.path.dirname(__file__), 'data', 'htmlpage.tpl.html')

    def __init__(self, stsdict):
        """Initialize a converter.

        Args:
            stsdict: an StsDict or a path-like object for a dictionary file.
        """
        if isinstance(stsdict, StsDict):
            self.table = stsdict
        else:
            _, ext = os.path.splitext(stsdict)
            if ext.lower() == '.jlist':
                self.table = Trie().load(stsdict, 'jlist')
            elif ext.lower() == '.tlist':
                self.table = Trie.loadjson(stsdict)
            else:  # default: list
                self.table = Trie().load(stsdict, 'plain')

    def convert(self, text, exclude=None):
        """Convert a text and yield each part.

        Yields:
            the next converted part as an StsDictConv, or an unmatched part as
            a str.
        """
        if exclude is None:
            yield from self.table.apply(text)
            return

        yield from self._convert_with_filter(text, exclude)

    def _convert_with_filter(self, text, exclude):
        index = 0
        for m in exclude.finditer(text):
            start, end = m.span(0)

            t = text[index:start]
            if t:
                yield from self.table.apply(t)

            for k, v in m.groupdict().items():
                if self.exclude_return_group_pattern.search(k) and v is not None:
                    t = v
                    break
            else:
                t = m.group(0)
            if t:
                yield StsConvExclude(text=t)

            index = end

        t = text[index:]
        if t:
            yield from self.table.apply(t)

    def convert_formatted(self, text, format=None, exclude=None):
        """Convert a text and yield each formatted part."""
        conv = self.convert(text, exclude=exclude)
        format = format if format is not None else 'txt'
        formatter = getattr(self, f'_convert_formatted_{format}')
        yield from formatter(conv)

    def _convert_formatted_txt(self, parts):
        for part in parts:
            if isinstance(part, str):
                yield part
            elif isinstance(part, StsConvExclude):
                yield part.text
            else:
                yield part.values[0]

    def _convert_formatted_txtm(self, parts, start='{{', end='}}', sep='->', vsep='|'):
        for part in parts:
            if isinstance(part, str):
                yield part
            elif isinstance(part, StsConvExclude):
                yield part.text
            else:
                olds, news = part
                old = ''.join(olds)

                if len(news) == 1 and old == news[0]:
                    yield f'{start}{old}{end}'
                else:
                    new = vsep.join(news)
                    yield f'{start}{old}{sep}{new}{end}'

    def _convert_formatted_html(self, parts):
        for part in parts:
            if isinstance(part, str):
                yield html.escape(part)
            elif isinstance(part, StsConvExclude):
                yield part.text
            else:
                olds, news = part
                old = ''.join(olds)
                content = f'<del hidden>{html.escape(old)}</del>'
                for i, v in enumerate(news):
                    hidden = '' if i == 0 else ' hidden'
                    content += f'<ins{hidden}>{html.escape(v)}</ins>'

                part = f'<a{" atomic" if len(olds) == 1 else ""}>{content}</a>'
                yield part

    def _convert_formatted_htmlpage(self, parts, template=None):
        if template is None:
            template = self.htmlpage_template

        try:
            fh = open(template, encoding='UTF-8', newline='')
        except TypeError:
            fh = nullcontext(template)

        with fh as fh:
            html = fh.read()

        pos = 0
        for m in self.template_placeholder_pattern.finditer(html):
            yield html[pos:m.start(0)]

            key = m.group(1)
            if key == '':
                yield '%'
            elif key == 'CONTENT':
                yield from self._convert_formatted_html(parts)
            elif key == 'VERSION':
                yield __version__

            pos = m.end(0)

        yield html[pos:]

    def _convert_formatted_json(self, parts, indent=None):
        encoder = json.JSONEncoder(
            indent=indent,
            separators=(',', ':') if indent is None else None,
            ensure_ascii=False, check_circular=False,
        )
        yield from encoder.iterencode(StreamList(parts))

    def convert_text(self, text, format=None, exclude=None):
        """Convert a text and return the result.

        Returns:
            a str of converted parts in the specified format.
        """
        conv = self.convert_formatted(text, format=format, exclude=exclude)
        return ''.join(conv)

    def convert_file(self, input=None, output=None,
                     input_encoding='UTF-8', output_encoding='UTF-8',
                     format=None, exclude=None):
        """Convert input and write to output.

        Args:
            input: a path-like, file-like, or None for stdin.
            output: a path-like, file-like, or None for stdout.
        """
        with file_input(input, encoding=input_encoding, newline='') as fh:
            text = fh.read()

        conv = self.convert_formatted(text, format=format, exclude=exclude)

        with file_output(output, encoding=output_encoding, newline='') as fh:
            for part in conv:
                fh.write(part)
