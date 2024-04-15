#!/usr/bin/env python3
"""An open library for flexible simplified-traditional Chinese text conversion.
"""
import html
import itertools
import json
import math
import os
import re
import sys
from collections import namedtuple
from contextlib import nullcontext

try:
    from functools import cached_property
except ImportError:
    # polyfill for Python < 3.8
    def cached_property(fn):
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


__version__ = '0.23.0'

StsDictMatch = namedtuple('StsDictMatch', ['conv', 'start', 'end'])
StsDictConv = namedtuple('StsDictConv', ['key', 'values'])


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
            elif is_ids and not (
                0x4E00 <= code <= 0x9FFF  # CJK unified
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
        """Split a text into a list of Unicode composites.
        """
        i = 0
        total = len(text)
        result = []
        while i < total:
            length = Unicode.composite_length(text, i)
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
        for key, values in dict(*args, **kwargs).items():
            self.add(key, values, skip_check=True)

    def __repr__(self):
        """Implementation of repr(self).
        """
        return f'{self.__class__.__name__}({repr(list(self.items()))})'

    def __getitem__(self, key):
        """Implementation of self[key].
        """
        return self._dict[key]

    def __contains__(self, item):
        """Implementation of "item in self".
        """
        return item in self._dict

    def __len__(self):
        """Implementation of len(self).
        """
        return len(self._dict)

    def __iter__(self):
        """Implementation of iter(self).
        """
        yield from self._dict

    def __eq__(self, other):
        """Implementation of "==" operator.
        """
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

    def keys(self):
        """Get a generator of keys.
        """
        yield from self._dict.keys()

    def values(self):
        """Get a generator of values.
        """
        yield from self._dict.values()

    def items(self):
        """Get a generator of key-values pairs.
        """
        yield from self._dict.items()

    def add(self, key, values, skip_check=False):
        """Add a key-values pair to this dictionary.

        Args:
            values: a string or a list of strings.
            skip_check: True to skip checking duplicated values.
        """
        values = [values] if isinstance(values, str) else values
        list_ = self._dict.setdefault(key, [])
        list_ += values if skip_check else [x for x in values if x not in list_]
        return self

    def update(self, stsdict, skip_check=False):
        """Add all key-values pairs from another StsDict or dict.

        Args:
            skip_check: True to skip checking duplicated values.
        """
        for key, values in stsdict.items():
            self.add(key, values, skip_check=skip_check)
        return self

    def load(self, *files):
        """Add all key-values pairs from plain-dict file(s).
        """
        for file in files:
            with open(file, 'r', encoding='UTF-8') as fh:
                for line in fh:
                    try:
                        key, values, *_ = line.rstrip('\n').split('\t')
                    except ValueError:
                        pass
                    else:
                        self.add(key, values.split(' '))
        return self

    def dump(self, file=None, sort=False):
        """Dump key-values pairs to a plain-dict file.

        Args:
            file: path of file to save. Use stdout if None.
            sort: True to sort the output.
        """
        it = self.items()
        if sort:
            it = sorted(it)
        with (
            open(file, 'w', encoding='UTF-8', newline='')
            if file
            else nullcontext(sys.stdout)
        ) as fh:
            for key, values in it:
                fh.write(f'{key}\t{" ".join(values)}\n')

    def loadjson(self, file):
        """Load from a JSON file.

        NOTE: The input data format may vary across subclasses.

        Returns:
            a new object with the same class.
        """
        with open(file, 'r', encoding='UTF-8') as fh:
            stsdict = self.__class__()
            stsdict._dict = json.load(fh)
        return stsdict

    def dumpjson(self, file=None, indent=None, sort=False):
        """Dump key-values pairs to a JSON file.

        NOTE: The output data format may vary across subclasses.

        Args:
            file: path of file to save. Use stdout if None.
            indent: indent the output with a specified integer.
            sort: True to sort the output.
        """
        with (
            open(file, 'w', encoding='UTF-8', newline='')
            if file
            else nullcontext(sys.stdout)
        ) as fh:
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
        for stsdict in stsdicts:
            newstsdict = newstsdict.join(stsdict)
        return newstsdict

    def join(self, stsdict):
        """Join another dictionary.

        Applying the returned dictionary to a text simulates the effect
        of applying using self and then using stsdict.

        This will invoke stsdict.apply_enum and it's recommended that stsdict
        be a Table or Trie for better performance.

        Returns:
            a new object with the same class.
        """
        dict1 = self._join_postfix(stsdict)
        dict2 = stsdict._join_prefix(self)
        return dict1.update(dict2)

    def _join_prefix(self, stsdict):
        """Prefix self with stsdict.

        Convert keys of self using the reversed stsdict, enumerating all
        possible matches.

        Yield a new key-value pair for the first value of an stsdict entry,
        e.g.:

            table:
                註冊表 => 登錄檔
            stsdict:
                注 => 註 注
            reversed stsdict:
                註 => 注
            table._join_prefix(stsdict):
                注冊表 => 登錄檔
                註冊表 => 登錄檔

        Yield a new minor key-value pair for each minor value of an stsdict
        entry, e.g.:

            table:
                註冊表 => 登錄檔
            stsdict:
                注 => 注 註
            reversed stsdict:
                註 => 注
            table._join_prefix(stsdict):
                註冊表 => 登錄檔
                注冊表 => 注冊表 登錄檔

        Returns:
            a new object with the same class.
        """
        dict_ = self.__class__()
        converter = self.__class__()
        converter_minor = self.__class__()
        for key, values in stsdict.items():
            for i, value in enumerate(values):
                if i == 0:
                    converter.add(value, [key])
                else:
                    converter_minor.add(value, [key])
        for key, values in self.items():
            for newkey in converter.apply_enum(key, include_short=True, include_self=True):
                dict_.add(newkey, values)
            for newkey in converter_minor.apply_enum(key, include_short=True, include_self=True):
                if newkey == key:
                    continue
                try:
                    assert dict_[newkey]
                except (KeyError, AssertionError):
                    dict_.add(newkey, newkey)
                dict_.add(newkey, values)
        return dict_

    def _join_postfix(self, stsdict):
        """Postfix self with stsdict.

        Convert values of self using stsdict, enumerating all maximal matches.
        Plus all conversions of stsdict.

        Example:
            table:
                因为 => 因爲
            stsdict:
                爲 => 為
            table._join_postfix(stsdict):
                因为 => 因為
                爲 => 為

        Returns:
            a new object with the same class.
        """
        dict_ = self.__class__()
        for key, values in self.items():
            for value in values:
                dict_.add(key, stsdict.apply_enum(value))
        return dict_.update(stsdict)

    def _split(self, parts):
        """Split parts into a list of Unicode composites.

        With automatic type handling.
        """
        if isinstance(parts, str):
            return Unicode.split(parts)
        elif isinstance(parts, list):
            return parts
        else:
            return list(parts)

    def match(self, parts, pos, maxpos=math.inf):
        """Match a unicode composite at pos.

        Args:
            parts: a string or iterable parts to be matched.

        Returns:
            an StsDictMatch or None if no match.
        """
        parts = self._split(parts)
        i = max(len(Unicode.split(key)) for key in self._dict)
        i = min(i, min(len(parts), maxpos) - pos)
        while i >= 1:
            end = pos + i
            current_parts = parts[pos:end]
            current = ''.join(current_parts)
            try:
                conv = StsDictConv(current_parts, self._dict[current])
            except KeyError:
                pass
            else:
                return StsDictMatch(conv, pos, end)
            i -= 1
        return None

    def apply(self, parts):
        """Convert text using the dictionary.

        Args:
            parts: a string or iterable parts to be converted.

        Yields:
            the next converted part as an StsDictConv, or an unmatched part as
            a str.
        """
        parts = self._split(parts)
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
            parts: a string or iterable parts to be converted.
            include_short: include non-maximal-match conversions
            include_self: include source for every match

        Returns:
            a list of possible conversions.
        """
        text = parts
        parts = self._split(parts)

        stack = [(parts, 0, 0)]
        substack = []
        results = {}
        while stack:
            (parts, matched, nextindex) = data = stack.pop()
            if nextindex < len(parts):
                self._apply_enum_sub(substack, data, include_short=include_short, include_self=include_self)
                while substack:
                    stack.append(substack.pop())
            elif matched > 0:
                results[''.join(parts)] = True

        results = list(results)

        if not results:
            results.append(text if isinstance(text, str) else ''.join(text))

        return results

    def _apply_enum_sub(self, stack, data, include_short=False, include_self=False):
        """Helper function of apply_enum
        """
        (parts, matched, index) = data
        has_atomic_match = False
        i = math.inf
        while i > index:
            match = self.match(parts, index, i)

            if match is None:
                break

            if match.end - index == 1:
                has_atomic_match = True

            values = match.conv.values
            if include_self:
                value = ''.join(match.conv.key)
                if value not in values:
                    values = itertools.chain(values, (value,))

            for value in values:
                result = parts[:index] + [value] + parts[match.end:]
                stack.append((result, matched + 1, index + 1))

            if not include_short:
                return

            i = match.end - 1

        # add atomic stepping (length = 1) case if none
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
            stack.append((parts, matched, index + 1))


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
    @cached_property
    def key_maxlen(self):
        """Get the maximal length of the keys.
        """
        return max(len(Unicode.split(key)) for key in self._dict)

    @cached_property
    def key_headchars(self):
        """Get a set of the first char of the keys.
        """
        return {key[0] for key in self._dict}

    def match(self, parts, pos, maxpos=math.inf):
        """Match a unicode composite at pos.

        Args:
            parts: a string or iterable parts to be matched.

        Returns:
            an StsDictMatch or None if no match.
        """
        parts = self._split(parts)
        if parts[pos][0] in self.key_headchars:
            i = self.key_maxlen
            i = min(i, min(len(parts), maxpos) - pos)
            while i >= 1:
                end = pos + i
                current_parts = parts[pos:end]
                current = ''.join(current_parts)
                try:
                    conv = StsDictConv(current_parts, self._dict[current])
                except KeyError:
                    pass
                else:
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
        """Implementation of self[key].
        """
        trie = self._dict
        try:
            for k in self._split(key):
                trie = trie[k]
            return trie['']
        except KeyError:
            raise KeyError(key)

    def __contains__(self, item):
        """Implementation of "item in self".
        """
        try:
            self[item]
        except KeyError:
            return False
        else:
            return True

    def __len__(self):
        """Implementation of len(self).
        """
        return sum(1 for _ in self)

    def __iter__(self):
        """Implementation of iter(self).
        """
        yield from self.keys()

    def keys(self):
        """Get a generator of keys.
        """
        def recurse(trie):
            for key in trie:
                if key == '':
                    yield ''.join(keystack)
                else:
                    keystack.append(key)
                    triestack.append(trie[key])
                    yield from recurse(triestack[-1])
            keystack.pop()
            triestack.pop()

        keystack = ['']
        triestack = [self._dict]
        yield from recurse(triestack[-1])

    def values(self):
        """Get a generator of values.
        """
        def recurse(trie):
            for key in trie:
                if key == '':
                    yield trie[key]
                else:
                    triestack.append(trie[key])
                    yield from recurse(triestack[-1])
            triestack.pop()

        triestack = [self._dict]
        yield from recurse(triestack[-1])

    def items(self):
        """Get a generator of key-values pairs.
        """
        def recurse(trie):
            for key in trie:
                if key == '':
                    yield ''.join(keystack), trie[key]
                else:
                    keystack.append(key)
                    triestack.append(trie[key])
                    yield from recurse(triestack[-1])
            keystack.pop()
            triestack.pop()

        keystack = ['']
        triestack = [self._dict]
        yield from recurse(triestack[-1])

    def add(self, key, values, skip_check=False):
        """Add a key-values pair to this dictionary.

        Args:
            values: a string or a list of strings.
            skip_check: True to skip checking duplicated values.
        """
        values = [values] if isinstance(values, str) else values

        current = self._dict
        for composite in Unicode.split(key):
            current = current.setdefault(composite, {})

        list_ = current.setdefault('', [])
        list_ += values if skip_check else [x for x in values if x not in list_]
        return self

    def match(self, parts, pos, maxpos=math.inf):
        """Match a unicode composite at pos.

        Args:
            parts: a string or iterable parts to be matched.

        Returns:
            an StsDictMatch or None if no match.
        """
        parts = self._split(parts)
        trie = self._dict
        i = pos
        total = min(len(parts), maxpos)
        match = None
        match_end = None
        while i < total:
            try:
                trie = trie[parts[i]]
            except KeyError:
                break
            try:
                match = trie['']
            except KeyError:
                pass
            else:
                match_end = i + 1
            i = i + 1
        if match:
            conv = StsDictConv(parts[pos:match_end], match)
            return StsDictMatch(conv, pos, match_end)
        return None


class StsMaker():
    """A class for making dictionary file(s).
    """
    config_dir = os.path.join(os.path.dirname(__file__), 'data', 'config')
    dictionary_dir = os.path.join(os.path.dirname(__file__), 'data', 'dictionary')

    def make(self, config_name, base_dir=None, output_dir=None,
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
                                        // file, relative to output_dir
                        "mode": "...",  // mode to handle the loaded sources:
                                        // load, swap, join
                        "src": ["...", ...]  // list of the source file paths,
                                             // should be .txt or .list files
                        "sort": true,   // truthy to sort the keys of the
                                        // generated dictionary
                        "include": "...",  // regex filter for output values
                        "exclude": "...",  // regex filter for output values
                    },
                    ...
                ]
            }

        Args:
            config_name: a str for the config file or name
            base_dir: a str for the base directory to parse the config path
                from config_name, or None for CWD
            output_dir: a str for the output directory, or None for
                the directory of the config file
            skip_check: truthy to generate every dictionary no matter that it's
                already up-to-date
            skip_requires: truthy to skip making from required configs
            quiet: truthy to skip reporting details

        Returns:
            a str for the path of the last generated dictionary file
        """
        # locate and load the config file
        config_file = self.get_config_file(config_name, base_dir=base_dir)
        config_dir = os.path.abspath(os.path.dirname(config_file))

        with open(config_file, 'r', encoding='UTF-8') as fh:
            config = json.load(fh)

        # handle required configs
        if not skip_requires:
            for cf in config.get('requires', []):
                self.make(cf, base_dir=config_dir, output_dir=output_dir, skip_requires=skip_requires, quiet=quiet)

        # make the requested dicts
        for dict_ in config['dicts']:
            dest = os.path.join(output_dir or config_dir, dict_['file'])
            format = os.path.splitext(dest)[1][1:].lower()
            mode = dict_['mode']
            files = [self.get_stsdict_file(f, base_dir=config_dir)
                     if isinstance(f, str)
                     else [self.get_stsdict_file(i, base_dir=config_dir) for i in f]
                     for f in dict_['src']]
            sort = dict_.get('sort', False)
            include = dict_.get('include', None)
            exclude = dict_.get('exclude', None)

            if include is not None:
                try:
                    include = re.compile(include)
                except re.error as exc:
                    raise ValueError(f'regex syntax error of the include filter: {exc}')

            if exclude is not None:
                try:
                    exclude = re.compile(exclude)
                except re.error as exc:
                    raise ValueError(f'regex syntax error of the exclude filter: {exc}')

            if not skip_check and not self.check_update(dest, files):
                if not quiet:
                    print(f'skip making (up-to-date): {dest}')
                continue

            if not quiet:
                print(f'making: {dest}')

            if mode == 'load':
                table = Table().load(*files)
            elif mode == 'swap':
                table = Table().load(*files).swap()
            elif mode == 'join':
                table = Table().load_filegroups(files)
            else:
                raise ValueError(f'Specified mode "{mode}" is not supported.')

            if include is not None or exclude is not None:
                _table = table
                table = Table()
                for key, values in _table.items():
                    values = [v for v in values
                              if (include is None or include.search(v))
                              and (exclude is None or not exclude.search(v))]
                    if values:
                        table.add(key, values)

            os.makedirs(os.path.dirname(dest), exist_ok=True)

            if format == 'tlist':
                Trie(table).dumpjson(dest, sort=sort)
            elif format == 'jlist':
                table.dumpjson(dest, sort=sort)
            else:  # default: list
                table.dump(dest, sort=sort)

        return dest

    def get_config_file(self, config, base_dir=None):
        """Calculate the path of a config file.

        1. Use it if it's an absolute path.
        2. Assume relative to base_dir or CWD.
        3. Assume relative to default config directory. (basename only; .json omissible)
        4. If not found, return 2.
        """
        if os.path.isabs(config):
            return config

        relative_config = os.path.join(base_dir, config) if base_dir is not None else config
        if os.path.isfile(relative_config):
            return relative_config

        if os.path.basename(config) == config:
            search_file = os.path.join(self.config_dir, config)
            if os.path.isfile(search_file):
                return search_file
            if not config.lower().endswith('.json'):
                search_file = os.path.join(self.config_dir, config + '.json')
                if os.path.isfile(search_file):
                    return search_file

        return relative_config

    def get_stsdict_file(self, stsdict, base_dir=None):
        """Calculate the path of a dictionary file.

        1. Use it if it's an absolute path.
        2. Assume relative to base_dir or CWD.
        3. Assume relative to default dictionary directory. (basename only)
        4. If not found, return 2.
        """
        if os.path.isabs(stsdict):
            return stsdict

        relative_stsdict = os.path.join(base_dir, stsdict) if base_dir is not None else stsdict
        if os.path.isfile(relative_stsdict):
            return relative_stsdict

        if os.path.basename(stsdict) == stsdict:
            search_file = os.path.join(self.dictionary_dir, stsdict)
            if os.path.isfile(search_file):
                return search_file

        return relative_stsdict

    def check_update(self, output, filegroups):
        """Check if the output file needs update.
        """
        if not os.path.isfile(output):
            return True

        for files in filegroups:
            if isinstance(files, str):
                files = [files]
            for file in files:
                if os.path.getmtime(file) > os.path.getmtime(output):
                    return True

        return False


class StsConverter():
    """Convert a text using an stsdict.
    """
    exclude_return_group_pattern = re.compile(r'^return\d*$')
    template_placeholder_pattern = re.compile(r'%(\w*)%')
    htmlpage_template = os.path.join(os.path.dirname(__file__), 'data', 'htmlpage.tpl.html')

    def __init__(self, stsdict):
        """Initialize a converter.

        Args:
            stsdict: an StsDict or a str, bytes or os.PathLike object for a
                dictionary file
        """
        if isinstance(stsdict, StsDict):
            self.table = stsdict
        else:
            _, ext = os.path.splitext(stsdict)
            if ext.lower() == '.jlist':
                self.table = Table().loadjson(stsdict)
            elif ext.lower() == '.tlist':
                self.table = Trie().loadjson(stsdict)
            else:  # default: list
                self.table = Table().load(stsdict)

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
                yield t

            index = end

        t = text[index:]
        if t:
            yield from self.table.apply(t)

    def convert_formatted(self, text, format=None, exclude=None):
        """Convert a text and yield each formatted part.
        """
        conv = self.convert(text, exclude=exclude)
        format = format if format is not None else 'txt'
        formatter = getattr(self, f'_convert_formatted_{format}')
        yield from formatter(conv)

    def _convert_formatted_txt(self, parts):
        for part in parts:
            if isinstance(part, str):
                yield part
            else:
                yield part[1][0]

    def _convert_formatted_txtm(self, parts, start='{{', end='}}', sep='->', vsep='|'):
        for part in parts:
            if isinstance(part, str):
                yield part
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
            else:
                olds, news = part
                old = ''.join(olds)
                content = f'<del hidden>{html.escape(old)}</del>'
                for i, v in enumerate(news):
                    hidden = '' if i == 0 else ' hidden'
                    content += f'<ins{hidden}>{html.escape(v)}</ins>'

                part = f"""<a>{content}</a>"""
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
            input: a file path or None for stdin.
            output: a file path or None for stdout.
        """
        with (
            open(input, 'r', encoding=input_encoding, newline='')
            if input
            else nullcontext(sys.stdin)
        ) as fh:
            text = fh.read()

        conv = self.convert_formatted(text, format=format, exclude=exclude)

        with (
            open(output, 'w', encoding=output_encoding, newline='')
            if output
            else nullcontext(sys.stdout)
        ) as fh:
            for part in conv:
                fh.write(part)
