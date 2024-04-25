### Config 配置檔

配置檔為 JSON 或 YAML 檔案（副檔名須為 `.yaml` 或 `.yml`）。規格如下：

```javascript
/**
 * @typedef {Object} configScheme
 * @property {string} [name] - name/description of the config
 * @property {string[]} [requires] - required configs, which are made before
 *     making from this config, as an absolute path, or a path relative to the
 *     directory of this config file, or the basename of a built-in config file
 *     (with or without extension ".json", ".yaml", ".yml")
 * @property {srcDictScheme[]} dicts - schemes of each dictionary file to be
 *     generated or loaded.
 */

/**
 * A dictScheme or string for a dict.
 *
 * The string should be an absolute path, or a path relative to the directory
 * of the config file, or the basename of a built-in dictionary file, with a
 * file extension of .txt, .list, .json, .jlist, .yaml, or .yml.
 *
 * @typedef {(string|dictScheme)} srcDictScheme
 */

/**
 * @typedef {Object} dictScheme
 * @property {string} [file] - path of the dictionary file to generate, as an
 *     absolute path, or a path relative to the directory of this config file.
 *     It should be a .tlist (compiled trie), .jlist (compiled table), or .list
 *     (plain text table). An unknown file extension is treated as .list. `src`
 *     must exist when omitted.
 * @property {string} [mode=load] - the mode to handle the loaded dicts.
 *     - "load" to simply merge the loaded keys and values;
 *     - "swap" to reverse the dict (i.e. use the values as keys and the keys
 *       as values);
 *     - "join" to chain dicts (a conversion using a dict joining dict1 and
 *       dict2 works like a conversion using dict1 and then dict2, but takes
 *       care of word segmentation);
 *     - "expand" to expand the placeholders (defined in the extra
 *       "placeholders" property) in the first dict with the matching key and
 *        values in other dicts;
 *     - "filter" to filter the output keys and values in the loaded dicts
 *       using extra "method", "include", and "exclude" properties.
 * @property {srcDictScheme[]} [src] - the source dicts. `file` must exist when
 *     omitted.
 * @property {boolean} [sort] - true to sort the keys of the output dictionary.
 * @property {boolean} [check] - true to raise an exception if the output
 *     contains an invalid char which will be loaded incorrectly. Set this
 *     when the output is a plain text table file and the source files contain
 *     untrusted JSON or YAML data that may include a char like " ", "\t",
 *     "\n", etc. in the dictionary.
 * @property {string[]} [placeholders] - strings to be expanded using other
 *     dicts. (for "expand" mode)
 * @property {string} [method=remove_key_values] - how to filter (for "filter"
 *     mode)
 *     - "remove_keys" to remove keys from the first dict if it appears in any
 *       other one;
 *     - "remove_key_values" to remove key-value pairs from the first dict if it
 *       appears in any other one.
 * @property {string} [include] - a regex filter that discards non-matched
 *     conversion values. (for "filter" mode)
 * @property {string} [exclude] - a regex filter that discards matched
 *     conversion values. (for "filter" mode)
 */
```

### Dictionary 詞典檔

原始詞典檔可為純文字、JSON、或 YAML。編譯產生的詞典檔有純文字（`.list`）、JSON列表（`.jlist`）、JSON樹（`.tlist`）三種格式，其中前二者可再作為原始檔輸入，後者則只能用於轉換。

#### 純文字

純文字詞典副檔名為 `.txt` 或 `.list`。規格為以 TAB 字元分隔輸入詞與轉換詞，多個轉換詞之間以半形空白分隔，如下：

```
輸入詞1\t轉換詞11 轉換詞12 ...
輸入詞2\t轉換詞21 轉換詞22 ...
...
```

注意，使用此格式時，輸入詞不可含有 TAB 字元，轉換詞不可含有半形空白字元。此外二者也不可含有換行等字元。

#### JSON

JSON 詞典副檔名為 `.json` 或 `.jlist`。規格如下：

```
{
  "輸入詞1": "轉換詞11",
  "輸入詞2": ["轉換詞21"],
  "輸入詞3": ["轉換詞31", "轉換詞32", ...],
  ...
}
```

#### YAML

YAML 詞典副檔名為 `.yaml` 或 `.yml`。規格如下：

```
輸入詞1: 轉換詞11
輸入詞2: [轉換詞21]
輸入詞3: [轉換詞31, 轉換詞32, ...]
...
```
