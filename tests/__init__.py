import os
import unittest

run_slow_tests = int(os.environ.get('STS_RUN_SLOW_TESTS', '0'))


def slow_test(reason='set envvar STS_RUN_SLOW_TESTS=1 to run slow tests'):
    return unittest.skipUnless(run_slow_tests, reason)
