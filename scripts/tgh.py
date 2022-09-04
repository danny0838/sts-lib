#!/usr/bin/env python3
"""處理通用規範漢字表
"""
import os

from sts import Table


def main():
    tgh = {}
    with open(os.path.join(__file__, '..', '..', 'sts', 'data', 'scheme', 'ts_tgh_convert.txt'), 'r', encoding='UTF-8') as f:
        for line in f:
            try:
                id, std, trad, vars, *_ = line.rstrip('\n').split('\t')
            except ValueError:
                continue
            tgh.setdefault(std, []).append((id, std, trad or None, list(vars)))

    # t2s
    table = Table().load(os.path.join(__file__, '..', '..', 'sts', 'data', 'dictionary', 'TSCharacters.txt'))
    for convs in tgh.values():
        for conv in convs:
            id, std, trad, vars = conv
            for var in vars:
                table.add(var, [std])
    table.dump(os.path.join(__file__, '..', '..', 'sts', 'data', 'dictionary', 'TSCharacters.txt'), sort=True)


if __name__ == '__main__':
    main()
