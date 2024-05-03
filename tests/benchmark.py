import json  # noqa: F401
import os
import tempfile
import timeit

from sts import StsConverter, StsMaker  # noqa: F401

root_dir = os.path.dirname(__file__)

build_stmt = """\
root = tempfile.mkdtemp(dir=tmpdir)
config_file = os.path.join(root, 's2twp.json')
with open(config_file, 'w', encoding='UTF-8') as fh:
    json.dump({
        'name': 'Simplified Chinese to Traditional Chinese (Taiwan standard) (with phrases)',
        'requires': [
            '_default'
        ],
        'dicts': [
            {
                'file': 's2twp.tlist',
                'mode': 'join',
                'src': [
                    {
                        'mode': 'load',
                        'src': [
                            'STPhrases.txt',
                            'STCharacters.txt',
                        ],
                    },
                    {
                        'mode': 'load',
                        'src': [
                            'TWPhrases.list',
                            'TWVariants.txt',
                        ],
                    },
                ],
            },
        ],
    }, fh)
StsMaker().make(config_file, quiet=True)
"""

load_setup = """\
root = tempfile.mkdtemp(dir=tmpdir)
config_file = os.path.join(root, 's2twp.json')
with open(config_file, 'w', encoding='UTF-8') as fh:
    json.dump({
        'name': 'Simplified Chinese to Traditional Chinese (Taiwan standard) (with phrases)',
        'requires': [
            '_default'
        ],
        'dicts': [
            {
                'file': 's2twp.tlist',
                'mode': 'join',
                'src': [
                    {
                        'mode': 'load',
                        'src': [
                            'STPhrases.txt',
                            'STCharacters.txt',
                        ],
                    },
                    {
                        'mode': 'load',
                        'src': [
                            'TWPhrases.list',
                            'TWVariants.txt',
                        ],
                    },
                ],
            },
        ],
    }, fh)
dict_file = StsMaker().make(config_file, quiet=True)
"""

load_stmt = """\
StsConverter(dict_file)
"""

convert_setup = """\
root = tempfile.mkdtemp(dir=tmpdir)
config_file = os.path.join(root, 's2twp.json')
with open(config_file, 'w', encoding='UTF-8') as fh:
    json.dump({
        'name': 'Simplified Chinese to Traditional Chinese (Taiwan standard) (with phrases)',
        'requires': [
            '_default'
        ],
        'dicts': [
            {
                'file': 's2twp.tlist',
                'mode': 'join',
                'src': [
                    {
                        'mode': 'load',
                        'src': [
                            'STPhrases.txt',
                            'STCharacters.txt',
                        ],
                    },
                    {
                        'mode': 'load',
                        'src': [
                            'TWPhrases.list',
                            'TWVariants.txt',
                        ],
                    },
                ],
            },
        ],
    }, fh)
dict_file = StsMaker().make(config_file, quiet=True)
converter = StsConverter(dict_file)
sample_file = os.path.join(root_dir, 'benchmark', 'zuozhuan.txt')
tmp_file = os.path.join(root, 'test.tmp')
"""

convert_stmt = """\
converter.convert_file(sample_file, tmp_file)
"""


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        # build
        number = 10
        repeat = 5
        t = timeit.repeat(build_stmt, repeat=repeat, number=number, globals={**globals(), **locals()})
        print(f'build ({number} loops) - average: {sum(t) / len(t)}, min: {min(t)}, max: {max(t)}')

        # load
        number = 200
        repeat = 5
        t = timeit.repeat(load_stmt, load_setup, repeat=repeat, number=number, globals={**globals(), **locals()})
        print(f'load ({number} loops) - average: {sum(t) / len(t)}, min: {min(t)}, max: {max(t)}')

        # convert
        number = 10
        repeat = 5
        t = timeit.repeat(convert_stmt, convert_setup, repeat=repeat, number=number, globals={**globals(), **locals()})
        print(f'convert ({number} loops) - average: {sum(t) / len(t)}, min: {min(t)}, max: {max(t)}')


if __name__ == '__main__':
    main()
