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
    'src': os.path.join(root, 'sts', 'data', 'scheme', 'traditional.tsv'),
    'fields': ['trad', 'vars', 'cn', 'tw', 'hk', 'jp', 'jpg', 'notes'],
    'fields_as_list': {'vars', 'cn', 'tw', 'hk', 'jp', 'jpg'},
    'has_header': True,
    'auto_sort': True,
}

scheme_st_multi_table = {
    'src': os.path.join(root, 'sts', 'data', 'scheme', 'st_multi.tsv'),
    'fields': ['simp', 'trads', 'notes', 'examples'],
    'fields_as_list': {'trads'},
}

scheme_ts_multi_table = {
    'src': os.path.join(root, 'sts', 'data', 'scheme', 'ts_multi.tsv'),
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
                    continue
            entry['cn'] = list(dict.fromkeys(simps + entry['cn']))

    table.save()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
        epilog=dedent(
            """\
            available methods (non-exhaustive):
              - tidy_tables: tidy table files like {traditional|st_multi|ts_multi}.tsv
            """
        ),
    )
    parser.add_argument(
        'method', nargs='?', default='merge_TSCharacters',
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
