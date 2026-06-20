# Changelog
* This project generally follows [semantic versioning](https://semver.org/). For a version `x.y.z`, `x` means a major (backward incompatible) change, `y` means a minor (backward compatible) change, and `z` means a patch (bug fix). Few versions may not strictly follow this rule due to historical reasons, though.
* Versions before 1.0 are in initial development. APIs are not stable for these versions, even a `y` version can involve a breaking change, and only partial notable changes are summarized in this document. See full commit history in the source repository for details.

## [0.39.3] - 2026-06-20
* Fixed missing config files in the package.

## [0.39.2] - 2026-06-19
* Fixed an issue where the `sort` command did not preserve extra fields separated by tabs.
* Fixed an issue where file type is not auto-detected when passing a path-like object to `StsDict.load`.
* Miscellaneous improvements to the internal code, test suite, and development tools.

## [0.39.1] - 2026-06-18
* Improved the web converter:
  * Improved `splitTerm` and fixed issues.
  * Added support for escaping special chars for custom dictionaries.
  * Added built time to the footer.
* Miscellaneous improvements to the internal code, development tools, CI/CD workflows, and documentation.

## [0.39.0] - 2026-06-14
* Added support for escaping special chars using `\xNN` (where NN is 00~7F) for text dictionaries.
* The `sort` command now preserves comments.
* Added `PyYAML` as primary dependency.
* Miscellaneous improvements to the internal code, test suite, and documentation.

## [0.38.0] - 2026-02-08
* Improved modularization of the package.
* Reworked processing message handling using native `logging` module.
* Miscellaneous improvements to the internal code, test suite, development tools, and documentation.

## [0.37.1] - 2026-01-31
* Miscellaneous fixes and improvements to the internal code, test suite, development tools, CI/CD workflows, and documentation.

## [0.37.0] - 2026-01-23
* Added support for the comment format since OpenCC 1.2.0.
* Added support for `--dict` (`-d`) option for `convert` subcommand.
* Miscellaneous improvements to the internal code.

## [0.36.0] - 2026-01-22
* Reworked `Trie` to be Unicode char based.
* Support pre-defined query using URL parameters for the web converter.

## [0.35.0] - 2026-01-09
* Dropped support for Python 3.7.
* Reworked package management using `pyproject.toml`.
* Miscellaneous improvements to the internal code, development tools, and CI/CD workflows.

## [0.32.0] - 2024-05-18
* Added support for `auto_space` config.
* Added support for new IDC in Unicode 15.1.

## [0.30.0] - 2024-04-30
* A dict entry whose value is an empty array is now never matched.
* Text excluded by a regex is now specially wrapped as a one-element array.
* Support dismissing a word and re-convert as a shorter word.

## [0.29.0] - 2024-04-25
* `?r??` (without `\t`) in a plain text dictionary is now treated as `?r??\t?r??`.

## [0.28.0] - 2024-04-24
* Removed `remove_keys` and `remove_values` modes, and merged them into `filter` mode.

## [0.27.1] - 2024-04-23
* Fixed possible index error for `expand` mode.
* Support expanding one key to multiple values for `expand` mode.

## [0.27.0] - 2024-04-23
* Added support for config using `.yaml` or `.yml` extension.
* Reworked the scheme of `config["dicts"]` to allow providing recursive dict scheme.
* `include` and `exclude` properties in a dict scheme now only works with mode `filter`.
* Added new modes `expand`, `remove_keys`, and `remove_values` for dict scheme.
* Added static web site builder.

## [0.24.0] - 2024-04-15
* Added support for loading `.json`, `.yaml`, or `.yml` as dict source.

## [0.21.0] - 2024-04-11
* Improved `htmlpage` output format to support interactive text inspection.
