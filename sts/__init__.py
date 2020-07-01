#!/usr/bin/env python3
"""An open library for simplified-traditional Chinese text conversion.
"""
import sys, os
import re
import argparse
import json
from glob import glob
import html
from collections import namedtuple, OrderedDict

__version__ = '0.14.0'
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

    This class is for child classes to implement on and not intended to be used
    directly.
    """
    def iter(self):
        """Get a generator of key-values pairs.
        """
        for key, values in self.items():
            yield key, values

    def add(self, key, values, skip_check=False):
        """Add a key-values pair to this dictionary.

        Args:
            values: a string or a list of values.
                ([value1, value2, value3, ...])
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
        """Add all key-values pairs from another dictionary.

        Args:
            skip_check: True to skip checking duplicated values.
        """
        for key, values in stsdict.iter():
            self.add(key, values, skip_check=skip_check)
        return self

    def load(self, *files):
        """Add key-values pairs from file(s) to the dictionary.
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
        """Dump key-values pairs to a text file.

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

        Returns:
            a new object with the same class.
        """
        with open(file, 'r', encoding='UTF-8') as f:
            stsdict = self.__class__(json.load(f))
            f.close()
        return stsdict

    def dumpjson(self, file=None, indent=None, sort=False):
        """Dump key-values pairs to a JSON file.

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
        """Search for keyword from all values.

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

    def load_fileslist(self, fileslist):
        """Load key-values pairs from a list of filelists.

        Returns:
            a new object with the same class.

        Args:
            fileslist: a list of dictionary lists.
            [
                [file1-1, file1-2, ...]
                [file2-1, file2-2, file2-3, ...]
                [file3-1, file3-2, file3-3, ...]
            ]
        """
        stsdicts = [self.__class__().load(*files) for files in fileslist]
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
        (Enumerate all matches.)

        Returns:
            a new object with the same class.

        e.g.
        self:
            註冊表 => 登錄檔
        stsdict:
            注 => 注 註
        swapped stsdict:
            注 => 注
            註 => 注
        self._join_prefix(stsdict):
            註冊表 => 登錄檔
            注冊表 => 登錄檔
        """
        dict_ = self.__class__()
        converter = stsdict.swap()
        for key, values in self.iter():
            dict_.add(key, values)
            for newkey in converter.apply_enum(key, no_short=False):
                dict_.add(newkey, values)
        return dict_

    def _join_postfix(self, stsdict):
        """Postfix self with stsdict.

        Convert values of self using stsdict.
        (Enumerate all maximal matches.)

        Returns:
            a new object with the same class.

        e.g.
        self:
            因为 => 因爲
        stsdict:
            爲 => 為
        self._join_postfix(stsdict):
            因为 => 因為
        """
        dict_ = self.__class__()
        for key, values in self.iter():
            for value in values:
                dict_.add(key, stsdict.apply_enum(value, no_short=True))
        dict_.add_dict(stsdict)
        return dict_

    def match(self, parts, pos):
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
        while i >= 1:
            end = pos + i
            current = "".join(parts[pos:end])
            if current in self:
                conv = StsDictConv(current, self[current])
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

    def apply_enum(self, parts, no_short=False):
        """Enumerate all possible conversions of text.

        Args:
            parts: a string or iterable parts to be converted.
            no_short: output conversions that are maximally-matched

        Returns:
            list: a list of possible conversions.

        e.g.
        table:
            干 => 干 乾
            于 => 于 於
            干于 => 甘芋 乾芋
        text:
            '干于'
        table.apply_enum(text, no_short=False):
            ['甘芋', '乾芋', '干于', '干於', '乾于', '乾於']
        table.apply_enum(text, no_short=True):
            ['甘芋', '乾芋']
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
        results = OrderedDict()
        while len(queue):
            (parts, matched, nextindex) = data = queue.pop(0)
            if nextindex < len(parts):
                queue += self._apply_enum_sub(data, no_short=no_short)
            elif matched > 0:
                results["".join(parts)] = True

        results = list(results)

        if len(results) == 0:
            results.append(text if text is not None else "".join(parts))

        return results

    def _apply_enum_sub(self, data, no_short=False):
        """Helper function of apply_enum

        Args:
            data: (parts, matched, index)

        Returns:
            [(value, matched, nextindex), ...]
        """
        (parts, matched, index) = data
        results = []
        if index < len(parts):
            match = self.match(parts, index)
            if match is not None:
                for value in match.conv.values:
                    result = parts[:index] + [value] + parts[match.end:]
                    results.append((result, matched + 1, match.end))

                if no_short:
                    return results

        if len(results) == 0:
            results.append((parts, matched, index + 1))

        return results

class Table(StsDict):
    """An STS dictionary with hash format.

    This class implements a cache and a head-char checking mechanism to improve
    performance on text conversion than base StsDict. The cache will not update
    after generated, and therefore the dictionary should not be modified after
    performing a text matching or conversion (match, apply, apply_enum, join,
    etc.) to avoid an unexpected behavior.
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

    def match(self, parts, pos):
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
            while i >= 1:
                end = pos + i
                current = "".join(parts[pos:end])
                if current in self:
                    conv = StsDictConv(current, self[current])
                    return StsDictMatch(conv, pos, end)
                i -= 1
        return None

class Trie(StsDict):
    """An STS dictionary with trie (prefix tree) format.

    Compared with hash, trie is faster for applying conversion,
    but takes more space and is slower to construct.
    """
    def iter(self):
        """Get a generator of key-values pairs.
        """
        def recurse(trie):
            for key in trie.keys():
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
            values: a string or a list of values.
                ([value1, value2, value3, ...])
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

    def match(self, parts, pos):
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
        total = len(parts)
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
            conv = StsDictConv("".join(parts[pos:match_end]), match)
            return StsDictMatch(conv, pos, match_end)
        return None

class StsListMaker():
    """A class for compling a dictionary.
    """
    def make(self, config, output_dir=None, quiet=False):
        """Compile a dictionary according to config.

        Load dictionaries specified in config and generate a new dictionary.

        scheme of config (.json):
        {
            "name": "...",
            "dicts": [{
                "file": "...",  // relative to config directory
                "type": "...", // list, jlist, tlist
                "mode": "...", // load, swap, join
                "src": ["...", ...] // list of .txt or .list files
            }, ...]
        }
        """
        def get_config_file(config):
            """Calculate the path of a config file.

            1. Use it if it's an absolute path.
            2. Assume relative to CWD. (.json omissible)
            3. Assume relative to config file. (.json omissible)
            4. If not found, assume relative to CWD.
            """
            if os.path.isabs(config):
                return config

            if os.path.isfile(config):
                return config
            for file in os.listdir():
                filebase, fileext = os.path.splitext(file)
                if filebase == config and fileext.lower() == '.json':
                    return file

            search_dir = os.path.normpath(os.path.join(__file__, '..', 'data', 'config'))
            search_file = os.path.join(search_dir, config)
            if os.path.isfile(search_file):
                return search_file
            for file in os.listdir(search_dir):
                filebase, fileext = os.path.splitext(file)
                if filebase == config and fileext.lower() == '.json':
                    return os.path.join(search_dir, file)

            return config

        def get_stsdict_path(stsdict):
            """Calculate the path of a dictionary file.

            1. Use it if it's an absolute path.
            2. Assume relative to config file directory. (.json omissible)
            3. Assume relative to dictionary directory. (.json omissible)
            4. If not found, assume relative to config file directory.
            """
            if os.path.isabs(stsdict):
                return stsdict

            search_path = os.path.abspath(os.path.join(config_dir, stsdict))
            if os.path.exists(search_path):
                return search_path

            search_path2 = os.path.abspath(os.path.join(dictionary_dir, stsdict))
            if os.path.exists(search_path2):
                return search_path2

            return search_path

        # Load config
        config_file = get_config_file(config)
        if not os.path.isfile(config_file):
            sys.exit(f'[error] specified config "{config}" is not a file')

        config_dir = os.path.abspath(os.path.dirname(config_file))
        dictionary_dir = os.path.abspath(os.path.join(__file__, '..', 'data', 'dictionary'))

        with open(config_file, "r", encoding="UTF-8") as f:
            config = json.load(f)
            f.close()

        def check_update(output, filegroups):
            if not os.path.isfile(output):
                return True

            for files in filegroups:
                if type(files) is str:
                    files = [files]
                for file in files:
                    if os.path.getmtime(file) > os.path.getmtime(output):
                        return True

            return False

        for dict_ in config['dicts']:
            dest = os.path.join(output_dir or config_dir, dict_['file'])
            format = dict_['format']
            mode = dict_['mode']
            files = [get_stsdict_path(f) if type(f) is str
                else [get_stsdict_path(i) for i in f]
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
                table = Table().load_fileslist(files)
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
            a generator of converted text content.
        """
        def parts_to_text(parts):
            for part in parts:
                if isinstance(part, str):
                    yield part
                else:
                    old, news = part

                    if self.options['mark']:
                        content = old + "->" + "|".join(news)

                        # plural > exact > single
                        if len(news) > 1:
                            part = "{{" + content + "}}"
                        elif old == news[0]:
                            part = "{{" + content + "}}"
                        elif len(news) == 1:
                            part = "{{" + content + "}}"
                        else:
                            part = news[0]
                    else:
                        part = news[0]

                    yield part

        def parts_to_html(parts):
            for part in parts:
                if isinstance(part, str):
                    yield html.escape(part)
                else:
                    old, news = part
                    content = f'<del hidden>{html.escape(old)}</del>'
                    for i, v in enumerate(news):
                        content += f'<ins{" hidden" if i else ""}>{html.escape(v)}</ins>'

                    # plural > exact > single
                    classes = []
                    if len(news) == 1:
                        classes.append('single')
                    if len(news) > 1:
                        classes.append('plural')
                    if old == news[0]:
                        classes.append('exact')

                    part = f'''<span tabindex="0" class="{' '.join(classes)}">{content}</span>'''
                    yield part


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

        if self.options['format'] == 'htmlpage':
            yield '''<!DOCTYPE html>
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
<pre contenteditable="true">'''
            yield from parts_to_html(conversion)
            yield '''</pre>
</body>
</html>'''
        elif self.options['format'] == 'html':
            yield from parts_to_html(conversion)
        elif self.options['format'] == 'json':
            yield json.dumps(list(conversion), ensure_ascii=False)
        else:  # default: format = 'txt'
            yield from parts_to_text(conversion)

    def convert_file(self, input=None, output=None):
        """Convert input and write to output.

        Args:
            input: a file path or None for stdin.
            output: a file path or None for stdout.
        """
        f = open(input, "r", encoding="UTF-8", newline="") if input else sys.stdin
        text = f.read()
        f.close()

        conversion = self.convert(text)

        f = open(output, "w", encoding="UTF-8", newline="") if output else sys.stdout
        for part in conversion:
            f.write(part)
        f.close()

    default_options={
        'format': 'txt',
        'mark': False,
        'exclude': None,
        }

def main():
    def sort(args):
        """Sort a conversion list.
        """
        input = args['input']
        output = args['output'] or args['input']

        Table().load(input).dump(output, sort=True)

    def swap(args):
        """Swap the key and value of a conversion list.
        """
        input = args['input']
        output = args['output'] or args['input']

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
        """Compile conversion dictionary(s).
        """
        configs = ['_default'] + args['config']
        dir = args['dir']
        quiet = args['quiet']

        for config in configs:
            StsListMaker().make(config, output_dir=dir, quiet=quiet)

    def convert(args):
        """Convert a file using the given config.
        """
        config = args['config']
        input = args['input']
        output = args['output']
        options={
            'format': args['format'],
            'mark': args['mark'],
            'exclude': args['exclude'],
            }

        StsListMaker().make('_default', quiet=True)
        stsdict = StsListMaker().make(config, quiet=True)
        converter = StsConverter(stsdict, options)
        converter.convert_file(input, output)

    # define the parsers
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default=False, action='store_true',
        help="""show version information and exit""")
    subparsers = parser.add_subparsers(dest='func', metavar='COMMAND')

    # subcommand: convert
    parser_convert = subparsers.add_parser('convert',
        help=convert.__doc__, description=convert.__doc__)
    parser_convert.add_argument('--config', '-c', default='s2t',
        help="""the conversion config to use (default: s2t)""")
    parser_convert.add_argument('--input', '-i', default=None,
        help="""file to convert (default: stdin)""")
    parser_convert.add_argument('--output', '-o', default=None,
        help="""file to save the output (default: stdout)""")
    parser_convert.add_argument('--format', '-f', default="txt",
        choices=['txt', 'html', 'htmlpage', 'json'], metavar='FORMAT',
        help="""output format (txt|html|htmlpage|json) (default: txt)""")
    parser_convert.add_argument('--mark', '-m', default=False, action='store_true',
        help="""mark converted chars for txt format""")
    parser_convert.add_argument('--exclude',
        help="""exclude text matching given regex from conversion, """
            """optionally also replace with its "return" subgroup"""
            )

    # subcommand: sort
    parser_sort = subparsers.add_parser('sort',
        help=sort.__doc__, description=sort.__doc__)
    parser_sort.add_argument('input', nargs='?',
        help="""file to sort""")
    parser_sort.add_argument('output', nargs='?',
        help="""file to save as (default: input)""")

    # subcommand: swap
    parser_swap = subparsers.add_parser('swap',
        help=swap.__doc__, description=swap.__doc__)
    parser_swap.add_argument('input', nargs='?',
        help="""file to swap""")
    parser_swap.add_argument('output', nargs='?',
        help="""file to save as (default: input)""")

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
    parser_make.add_argument('config', nargs='*',
        help="""the config file(s) to compile (default: built-in compile)""")
    parser_make.add_argument('--dir', '-d', default=None,
        help="""the directory to save the output (default: config directory)""")
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
