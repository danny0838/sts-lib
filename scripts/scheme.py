#!/usr/bin/env python3
"""Handle scheme files."""
import argparse
import csv
import os
from contextlib import contextmanager
from functools import reduce
from textwrap import dedent

root = os.path.normpath(os.path.join(__file__, '..', '..'))

csv.register_dialect('char-table', delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE)

scheme_trad_table = {
    'src': os.path.join(root, 'sts', 'data', 'scheme', 'chars.tsv'),
    'fields': ['trad', 'vars', 'cn', 'tw', 'hk', 'jp', 'jpg', 'notes'],
    'fields_as_list': {'vars', 'cn', 'tw', 'hk', 'jp', 'jpg'},
    'has_header': True,
    'auto_sort': True,
}

scheme_st_multi_table = {
    'src': os.path.join(root, 'sts', 'data', 'scheme', 'chars_s2t.tsv'),
    'fields': ['simp', 'trads', 'notes', 'examples'],
    'fields_as_list': {'trads'},
}

scheme_ts_multi_table = {
    'src': os.path.join(root, 'sts', 'data', 'scheme', 'chars_t2s.tsv'),
    'fields': ['trad', 'simps', 'notes', 'examples'],
    'fields_as_list': {'simps'},
}


class CharTable(dict):
    """Extended dict to allow custom attributes."""
    def __init__(self, scheme=None, **kwargs):
        super().__init__()
        scheme = scheme or kwargs
        self.src = scheme['src']
        self.fields = scheme['fields']
        self.fields_as_list = scheme.get('fields_as_list', set())
        self.dialect = scheme.get('dialect', 'char-table')
        self.has_header = scheme.get('has_header', False)
        self.auto_sort = scheme.get('auto_sort', False)

    @contextmanager
    def open(self, mode='r'):
        if mode == 'r':
            with open(self.src, encoding='UTF-8') as fh:
                reader = csv.DictReader(fh, fieldnames=self.fields, restval='', dialect=self.dialect)
                yield self._open_reader(reader)
        elif mode == 'w':
            with open(self.src, 'w', encoding='UTF-8') as fh:
                writer = csv.DictWriter(fh, fieldnames=self.fields, extrasaction='ignore', dialect=self.dialect)
                if self.has_header:
                    writer.writeheader()
                yield writer
        else:
            raise ValueError(f'unsupported mode: {mode}')

    def _open_reader(self, reader):
        # skip an optional header row
        if self.has_header:
            reader = self._open_iterrows(reader)

        for row in reader:
            for field in self.fields_as_list:
                row[field] = list(dict.fromkeys(v for v in row[field].split(' ') if v))
            yield row

    def _open_iterrows(self, reader):
        header = next(reader, None)
        if header and list(header.values()) != self.fields:
            yield header
        yield from reader

    def load(self):
        with self.open() as reader:
            for row in reader:
                self.setdefault(next(iter(row.values())), row)
        return self

    def save(self):
        with self.open('w') as writer:
            keys = sorted(self) if self.auto_sort else self.keys()
            for key in keys:
                row = self[key]
                _row = {
                    k: (' '.join(v) if k in self.fields_as_list else v)
                    for k, v in row.items()
                }
                writer.writerow(_row)


def tidy_trad_table():
    table = CharTable(scheme_trad_table).load()
    for entry in table.values():
        entry['vars'] = [v for v in entry['vars'] if v not in table]
    table.save()
    return table


def tidy_st_multi_table():
    table = CharTable(scheme_st_multi_table).load()
    table.save()
    return table


def tidy_ts_multi_table():
    table = CharTable(scheme_ts_multi_table).load()
    table.save()
    return table


def tidy_tables():
    tidy_trad_table()
    tidy_st_multi_table()
    tidy_ts_multi_table()


def merge_STCharacters_to_st_multi():  # noqa: N802
    table = CharTable(scheme_st_multi_table).load()

    with CharTable(
        src=os.path.join(root, 'sts', 'data', 'dictionary', 'STCharacters.txt'),
        fields=['simp', 'trads'],
        fields_as_list={'trads'},
    ).open() as reader:
        for row in reader:
            simp = row['simp']
            trads = row['trads']
            try:
                entry = table[simp]
            except KeyError:
                if len(trads) > 1:
                    table[simp] = {'simp': simp, 'trads': trads}
            else:
                entry['trads'] = trads

    table.save()


def merge_ts_multi():
    table = CharTable(scheme_trad_table).load()

    table_ts = CharTable(scheme_ts_multi_table).load()
    for row in table_ts.values():
        trad = row['trad']
        simps = row['simps']
        try:
            entry = table[trad]
        except KeyError:
            table[trad] = {'trad': trad, 'cn': simps}
        else:
            entry['cn'] += [v for v in simps if v not in entry['cn']]

    table.save()


def merge_st_multi():
    table = CharTable(scheme_trad_table).load()

    table_st = CharTable(scheme_st_multi_table).load()
    for row in table_st.values():
        simp = row['simp']
        trads = row['trads']
        for trad in trads:
            try:
                entry = table[trad]
            except KeyError:
                table[trad] = {'trad': trad, 'cn': [simp]}
            else:
                if simp not in entry['cn']:
                    entry['cn'].append(simp)

    table.save()


def merge_STCharacters():  # noqa: N802
    table = CharTable(scheme_trad_table).load()

    with CharTable(
        src=os.path.join(root, 'sts', 'data', 'dictionary', 'STCharacters.txt'),
        fields=['simp', 'trads'],
        fields_as_list={'trads'},
    ).open() as reader:
        for row in reader:
            simp = row['simp']
            trads = row['trads']
            for trad in trads:
                try:
                    entry = table[trad]
                except KeyError:
                    table[trad] = {'trad': trad, 'cn': [simp]}
                else:
                    if simp not in entry['cn']:
                        entry['cn'].append(simp)

    table.save()


def merge_TSCharacters():  # noqa: N802
    table = CharTable(scheme_trad_table).load()

    table_st = {}
    for trad, entry in table.items():
        for simp in entry['cn']:
            table_st.setdefault(simp, []).append(trad)

    def find_newtrad_reducer(acc, cur):
        for k in list(acc):
            if k not in cur:
                del acc[k]
        return acc

    def find_newtrad(simps):
        # search for a common traditional char of simps
        newtrads_dicts = [dict.fromkeys(table_st.get(simp, [])) for simp in simps]
        newtrads = reduce(find_newtrad_reducer, newtrads_dicts)
        if newtrads:
            return next(iter(newtrads))

        # search for a simp that is defined as a traditional char
        for simp in simps:
            if simp in table:
                return simp

        return None

    with CharTable(
        src=os.path.join(root, 'sts', 'data', 'dictionary', 'TSCharacters.txt'),
        fields=['trad', 'simps'],
        fields_as_list={'simps'},
    ).open() as reader:
        for row in reader:
            trad = row['trad']
            simps = row['simps']
            try:
                entry = table[trad]
            except KeyError:
                # trad is not defined as traditional and may be a variant of
                # another traditional char. Try to find the appropriate
                # traditional char.
                newtrad = find_newtrad(simps)
                if newtrad:
                    entry = table[newtrad]
                    print(f'taking {newtrad} as traditional and {trad} as variant')
                    if trad not in entry['vars']:
                        entry['vars'].append(trad)
                else:
                    print(f'adding {trad} as new traditional')
                    entry = table[trad] = {'trad': trad, 'cn': simps}
            entry['cn'] = list(dict.fromkeys(simps + entry['cn']))

    table.save()


def merge_Variants(src, field):  # noqa: N802
    table = CharTable(scheme_trad_table).load()

    with CharTable(
        src=src,
        fields=['trad', 'stds'],
        fields_as_list={'stds'},
    ).open() as reader:
        for row in reader:
            trad = row['trad']
            stds = row['stds']
            try:
                entry = table[trad]
            except KeyError:
                entry = table[trad] = {'trad': trad, field: stds}
            else:
                entry[field] = [v for v in stds if v not in entry[field]] + entry[field]

    table.save()


def merge_TWVariants():  # noqa: N802
    src = os.path.join(root, 'sts', 'data', 'dictionary', 'TWVariants.txt')
    merge_Variants(src, 'tw')


def merge_HKVariants():  # noqa: N802
    src = os.path.join(root, 'sts', 'data', 'dictionary', 'HKVariants.txt')
    merge_Variants(src, 'hk')


def merge_JPVariants():  # noqa: N802
    src = os.path.join(root, 'sts', 'data', 'dictionary', 'JPVariants.txt')
    merge_Variants(src, 'jp')


def merge_tgh_t2s():
    tgh_conv = {}
    with CharTable(
        src=os.path.join(root, 'sts', 'data', 'scheme', 'cn_tgh_convert.tsv'),
        fields=['id', 'std', 'trad', 'vars'],
        fields_as_list={'vars'},
    ).open() as reader:
        for row in reader:
            row['trad'] = row['trad'] or None
            tgh_conv.setdefault(row['id'], {})[row['trad']] = row

    tgh_list = {}
    with CharTable(
        src=os.path.join(root, 'sts', 'data', 'scheme', 'cn_tgh_list.tsv'),
        fields=['id', 'std'],
    ).open() as reader:
        for row in reader:
            try:
                tgh_list[row['id']] = tgh_conv[row['id']]
            except KeyError:
                row['trad'] = None
                row['vars'] = []
                tgh_list.setdefault(row['id'], {})[row['std']] = row

    tgh_table = {}
    for dict_ in tgh_list.values():
        for trad, entry in dict_.items():
            trad = entry['trad'] or entry['std']
            tgh_table[trad] = {
                'trad': trad,
                'vars': entry.get('vars', []),
                'std': entry['std'],
            }

    trad_table = CharTable(scheme_trad_table).load()

    for trad, entry in tgh_table.items():
        trad = entry['trad']
        std = entry['std']

        if trad == std:
            if trad not in trad_table:
                trad_table[trad] = {'trad': trad, 'cn': [std]}

    trad_table.save()


def merge_jp_std():
    trad_table = CharTable(scheme_trad_table).load()

    trad_table_v2t = {}
    for trad, entry in trad_table.items():
        for var in entry['vars']:
            if var != trad and var not in trad_table:
                trad_table_v2t[var] = trad

    jp_std2trad = {}

    with CharTable(
        src=os.path.join(root, 'sts', 'data', 'scheme', 'jp_jouyou.tsv'),
        fields=['std', 'olds', 'year'],
        fields_as_list={'olds'},
    ).open() as reader:
        for row in reader:
            std = row['std']
            trads = row['olds']
            jp_std2trad.setdefault(std, []).extend(trads)

    with CharTable(
        src=os.path.join(root, 'sts', 'data', 'scheme', 'jp_jinmeiyou.tsv'),
        fields=['std'],
    ).open() as reader:
        for row in reader:
            std = row['std']
            jp_std2trad.setdefault(std, [])

    for std, trads in jp_std2trad.items():
        old = None
        for trad in trads:
            try:
                newtrad = trad_table_v2t[trad]
            except KeyError:
                pass
            else:
                print(f"""taking "{newtrad}" instead of "{trad}" as traditional (the latter is defined as a variant)""")
                old = trad
                trad = newtrad

            try:
                entry = trad_table[trad]
            except KeyError:
                try:
                    entry = trad_table[std]
                except KeyError:
                    entry = trad_table[trad] = {'trad': trad, 'jp': [std]}
                else:
                    print(f"""taking "{std}" instead of "{trad}" as traditional (the former is defined as a standard)""")
                    if std not in entry['jp']:
                        entry['jp'].append(std)
                    if trad not in entry['jpg']:
                        entry['jpg'].append(trad)
                    continue

            if std not in entry['jp']:
                entry['jp'].append(std)

            if old and old not in entry['jpg']:
                entry['jpg'].append(old)

    trad_table.save()


def make_dicts():
    """Validate scheme files and make dictionary files from them."""
    def validate_t2x_multi(x, table_main_t2x):
        src = os.path.join(root, 'sts', 'data', 'scheme', f'chars_t2{x}.tsv')

        print(f'validating: {src}')
        if not os.path.isfile(src):
            return {}

        table_t2x = CharTable(
            src=src,
            fields=['trad', 'stds', 'notes', 'examples'],
            fields_as_list={'stds'},
        ).load()
        for key in list(table_t2x):
            row = table_t2x[key]
            trad = row['trad']
            stds = row['stds']

            try:
                stds_main = table_main_t2x[trad]
            except KeyError:
                print(f'WARNING: undefined trad char {repr(trad)}')
                del table_t2x[trad]
                continue

            extra = [v for v in stds if v not in stds_main]
            if extra:
                print(f'WARNING: undefined standard chars {extra} for trad char {repr(trad)}')
                for v in extra:
                    stds.remove(v)

        table_t2x.save()
        return table_t2x

    def validate_x2t_multi(x, table_main_x2t):
        src = os.path.join(root, 'sts', 'data', 'scheme', f'chars_{x}2t.tsv')

        print(f'validating: {src}')
        if not os.path.isfile(src):
            return {}

        table_x2t = CharTable(
            src=src,
            fields=['std', 'trads', 'notes', 'examples'],
            fields_as_list={'trads'},
        ).load()
        for key in list(table_x2t):
            row = table_x2t[key]
            std = row['std']
            trads = row['trads']

            try:
                trads_main = table_main_x2t[std]
            except KeyError:
                print(f'WARNING: undefined standard char {repr(std)}')
                del table_x2t[std]
                continue

            extra = [v for v in trads if v not in trads_main]
            if extra:
                print(f'WARNING: undefined trad chars {extra} for standard char {repr(std)}')
                for v in extra:
                    trads.remove(v)

        table_x2t.save()
        return table_x2t

    def make_t2x_dict(filename, x, fields, hook=None):
        table_main_t2x = {}
        for entry in table_main.values():
            trad = entry['trad']
            vars = entry['vars']
            for t in [trad] + vars:
                table_main_t2x[t] = reduce(lambda a, c: a + entry[c], fields, []) or [trad]

        table_t2x = validate_t2x_multi(x, table_main_t2x)

        for trad, stds in table_main_t2x.items():
            try:
                entry = table_t2x[trad]
            except KeyError:
                stds = list(stds)
            else:
                stds = entry['stds']
            table_main_t2x[trad] = stds

        if callable(hook):
            hook(table_main_t2x)

        dst = os.path.join(root, 'sts', 'data', 'dictionary', filename)
        print(f'making {dst}')
        with CharTable(
            src=dst,
            fields=['trad', 'stds'],
            fields_as_list={'stds'},
        ).open('w') as writer:
            for trad in sorted(table_main_t2x):
                stds = table_main_t2x[trad]
                if stds == [trad]:
                    continue
                if stds:
                    writer.writerow({'trad': trad, 'stds': ' '.join(stds)})

    def make_x2t_dict(filename, x, fields):
        table_main_x2t = {}
        for entry in table_main.values():
            trad = entry['trad']
            for std in reduce(lambda a, c: a + entry[c], fields, []):
                table_main_x2t.setdefault(std, {})[trad] = None

        table_x2t = validate_x2t_multi(x, table_main_x2t)

        for std, trads in table_main_x2t.items():
            try:
                entry = table_x2t[std]
            except KeyError:
                trads = list(trads)
            else:
                trads = entry['trads']
            table_main_x2t[std] = trads

        dst = os.path.join(root, 'sts', 'data', 'dictionary', filename)
        print(f'making: {dst}')
        with CharTable(
            src=dst,
            fields=['std', 'trads'],
            fields_as_list={'trads'},
        ).open('w') as writer:
            for std in sorted(table_main_x2t):
                trads = table_main_x2t[std]
                if trads == [std]:
                    continue
                if trads:
                    writer.writerow({'std': std, 'trads': ' '.join(trads)})

    # load and validate main table
    table_main = tidy_trad_table()

    # validate multi table and make dict files
    make_t2x_dict('TSCharacters.txt', 's', ['cn'])
    make_x2t_dict('STCharacters.txt', 's', ['cn'])
    make_t2x_dict('TWVariants.txt', 'tw', ['tw'])
    make_x2t_dict('TWVariantsRev.txt', 'tw', ['tw'])
    make_t2x_dict('HKVariants.txt', 'hk', ['hk'])
    make_x2t_dict('HKVariantsRev.txt', 'hk', ['hk'])
    make_t2x_dict('JPVariants.txt', 'jp', ['jp'])
    make_x2t_dict('JPVariantsRev.txt', 'jp', ['jp'])


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
        epilog=dedent(
            """\
            available methods (non-exhaustive):
              - tidy_tables: tidy table files like {traditional|st_multi|ts_multi}.tsv
              - make_dicts: validate table files and build dictionary files
            """
        ),
    )
    parser.add_argument(
        'method', nargs='?', default='merge_jp_std',
        help="""method to execute (default: %(default)s)""",
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()
    try:
        method = globals()[args.method]
    except KeyError:
        raise ValueError(f'unknown method: {args.method}') from None
    else:
        method()


if __name__ == '__main__':
    main()
