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
            tgh.setdefault(id, []).append((id, std, trad or None, list(vars)))

    table1 = Table().load(os.path.join(__file__, '..', '..', 'sts', 'data', 'dictionary', 'TSCharacters.txt'))
    table2 = Table().load(os.path.join(__file__, '..', '..', 'sts', 'data', 'dictionary', 'STCharacters.txt'))
    for convs in tgh.values():
        for conv in convs:
            id, std, trad, vars = conv
            if trad and trad != std:
                table1.add(trad, [std])
                table2.add(std, [trad])
    table1.dump(os.path.join(__file__, '..', '..', 'sts', 'data', 'dictionary', 'TSCharacters.txt'), sort=True)
    table2.dump(os.path.join(__file__, '..', '..', 'sts', 'data', 'dictionary', 'STCharacters.txt'), sort=True)


if __name__ == '__main__':
    main()
