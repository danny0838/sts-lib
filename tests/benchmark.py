import inspect
import os
import tempfile
import timeit

from sts import StsConverter, StsMaker

root_dir = os.path.dirname(__file__)


def benchmark_build():
    def func():
        StsMaker().make(config, skip_check=True, quiet=True)

    config = 's2twp'
    StsMaker().make(config, quiet=True)

    benchmark(func, number=2, repeat=3)


def benchmark_load():
    def func():
        StsConverter(dict_file)

    dict_file = StsMaker().make('s2twp', quiet=True)
    benchmark(func, number=20, repeat=3)


def benchmark_convert():
    def func():
        converter.convert_file(sample_file, tmp_file)

    dict_file = StsMaker().make('s2twp', quiet=True)
    converter = StsConverter(dict_file)
    sample_file = os.path.join(root_dir, 'benchmark', 'zuozhuan.txt')
    with tempfile.TemporaryDirectory() as root:
        tmp_file = os.path.join(root, 'test.tmp')

        benchmark(func, number=2, repeat=3)


def benchmark(stmt='pass', setup='pass', number=1, repeat=1, globals=None):
    # get name of the caller function
    funcname = inspect.stack()[1].function

    t = timeit.repeat(stmt=stmt, setup=setup, number=number, repeat=repeat, globals=globals)
    if repeat > 1:
        print(f'{funcname} ({number} loops) - average: {sum(t) / len(t)}, min: {min(t)}, max: {max(t)}')
    else:
        print(f'{funcname} ({number} loops) - {sum(t)}')


def main():
    benchmark_build()
    benchmark_load()
    benchmark_convert()


if __name__ == '__main__':
    main()
