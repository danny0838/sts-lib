## Unit Test

Enter this project directory and install it (adding `-e` is recommended):

    pip install -e .[dev]

Perform the unit tests:

    python -m unittest -v

By default slow tests are not run. Set envvar `STS_RUN_SLOW_TESTS=1` to include them.
