#!/usr/bin/env python3
"""處理通用規範漢字表
"""
import sys
import os
import re
import json
from sts import StsDict, Table

def main():
    tgh = {}
    with open(os.path.join(__file__, '..', '..', 'sts', 'data', 'scheme', 'ts_tgh_list.txt'), 'r', encoding='UTF-8') as f:
        for line in f:
            try:
                id, char, *_ = line.split()
            except ValueError:
                pass
            tgh[char] = id

    # t2s
    table = Table().load(os.path.join(__file__, '..', '..', 'sts', 'data', 'dictionary', 'TSCharactersEx.txt'))

    table2 = Table()
    for key, values in table.items():
        if key in tgh:
            values = [key] + values
        table2.add(key, values)
    table2.dump(os.path.join(__file__, '..', '..', 'sts', 'data', 'dictionary', 'TSCharactersEx.txt'))

if __name__ == "__main__":
    main()