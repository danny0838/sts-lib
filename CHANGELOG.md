# Changelog
* This project generally follows [semantic versioning](https://semver.org/). For a version `x.y.z`, `x` means a major (backward incompatible) change, `y` means a minor (backward compatible) change, and `z` means a patch (bug fix). Few versions may not strictly follow this rule due to historical reasons, though.
* Versions before 1.0 are in initial development. APIs are not stable for these versions, even a `y` version can involve a breaking change, and only partial notable changes are summarized in this document. See full commit history in the source repository for details.

## [0.28.0] - 2024-04-24
* Removed `remove_keys` and `remove_values` modes, and merged them into `filter` mode.

## [0.27.1] - 2024-04-23
* Fixed possible index error for `expand` mode.
* Support expanding one key to multiple values for `expand` mode.

## [0.27.0] - 2024-04-23
* Added support of config using `.yaml` or `.yml` extension.
* Reworked the scheme of `config["dicts"]` to allow providing recursive dict scheme.
* `include` and `exclude` properties in a dict scheme now only works with mode `filter`.
* Added new modes `expand`, `remove_keys`, and `remove_values` for dict scheme.
* Added static web site builder.

## [0.24.0] - 2024-04-15
* Added support of loading `.json`, `.yaml`, or `.yml` as dict source.

## [0.21.0] - 2024-04-11
* Improved `htmlpage` output format to support interactive text inspection.
