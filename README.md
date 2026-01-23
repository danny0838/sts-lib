# STS 簡繁祕書

![PyPI version](https://img.shields.io/pypi/v/sts-lib)
![Python Versions](https://img.shields.io/pypi/pyversions/sts-lib)
![Status](https://img.shields.io/pypi/status/sts-lib)
![License](https://img.shields.io/github/license/danny0838/sts-lib)

STS (Simplified-Traditional Secretary) is an open library for flexible simplified-traditional Chinese text conversion.

簡繁祕書是開源、輕巧、有彈性的中文簡繁轉換工具，也支援異體字轉換及地區慣用詞轉換。


## Features 特色

* 支援 [OpenCC](https://github.com/BYVoid/OpenCC) 格式及 JSON、YAML 格式的詞典檔。
* 可透過配置檔組合多個詞典檔作為具體轉換方案。組合詞典可儲存成新詞典檔以加速未來載入使用，任一詞典檔更新時皆會自動重新生成組合詞典。支援的組合方式有「並聯」、「串聯」、「反轉」、「展開」、「篩選」等等。
* 簡繁對應、異體字對應、地區慣用詞對應等不同的對應關係皆區分至不同的詞典檔。
* 詞典及配置檔與程式本體分離，可自由修改、擴充。
* 支援一對多轉換，轉換結果可輸出為純文字、HTML、JSON 等格式。
* 支援 Unicode 組合字，例如「⿰虫鬼」視為一個字，不會因為詞典有「虫=>蟲」而被轉為「⿰蟲鬼」。
* 支援用正規表示式略過特定文字的轉換。
* 支援編碼轉換，可自訂輸入及輸出檔案的字元編碼。


## Usage 使用

### Installation 安裝

安裝 Python >= 3.8 ([官網](https://www.python.org/))，然後在命令列輸入以下指令安裝（或升級至）最新版本：
```
python -m pip install -U sts-lib
```

> 若要支援 YAML 格式，須額外安裝 PyYAML 套件，或改用以下指令安裝：
> ```
> python -m pip install -U sts-lib[yaml]
> ```

### Command Line

* `sts --help` 或 `sts COMMAND --help` 檢視可用指令的詳細說明文檔。

* `sts convert [OPTIONs] [file ...]` 執行簡繁轉換：
  * `file` 為一或多個欲轉換的檔案。（省略則讀取標準輸入 STDIN）
  * `-c CONFIG` 指定轉換用的配置檔，可為內建配置檔名稱或自製配置檔（JSON 或 YAML）的路徑。可用的內建配置檔詳見 [sts/data/config](https://github.com/danny0838/sts-lib/tree/master/sts/data/config) 目錄，可簡寫，例如可輸入 `s2t` 代表使用 `sts/data/config/s2t.json`。
  * `-d DICT` 指定轉換用的詞典檔。可用 `sts make ...` 從配置檔生成詞典檔。覆蓋 `-c`。
  * `-f FORMAT` 指定輸出格式，可用格式如下：
    * `txt`：純文字，適合一般使用。
    * `txtm`：純文字加轉換標示。
    * `html`：加上 HTML 標記的文本，可嵌入至網頁應用程式做互動式校對。
    * `htmlpage`：加入 HTML 樣式的網頁，可直接開啟做互動式校對。
    * `json`：以 JSON 格式表示轉換輸出，可用其他程式進一步解析處理。
  * `--exclude PATTERN` 指定用於忽略簡繁轉換的正規表示式。有指定 `return`（或 `return1`, `return2`, ... 等）子群組時會取代為子群組的值。
    * 例如 `sts convert -c s2twp --exclude "「.*?」"` 會把 `「程序」正义` 轉換為 `「程序」正義`。
    * 例如 `sts convert -c s2twp --exclude "-{(?P<return>.*?)}-"` 會把 `-{程序}-正义` 轉換為 `程序正義`。
  * `--in-enc ENCODING` 指定輸入編碼。可用編碼參見[這裡](https://docs.python.org/3/library/codecs.html#standard-encodings)。
  * `--out-enc ENCODING` 指定輸出編碼。可用編碼參見[這裡](https://docs.python.org/3/library/codecs.html#standard-encodings)。
  * `-o OUTPUT` 可重覆多次，指定對應輸入檔案轉換結果的輸出路徑。（無對應者輸出至原檔）
  * `--stdout` 將所有轉換結果輸出至標準輸出 STDOUT。

### Python

```python
from sts import StsMaker, StsConverter

# generate a dictionary file from a config and get its path
dictfile = StsMaker().make('s2t', quiet=True)

# initialize a converter from the dictionary file
converter = StsConverter(dictfile)

# perform conversion for a string
converter.convert_text('汉字', format='txt', exclude=None)  # 漢字

# perform conversion for a file (None for stdin/stdout)
converter.convert_file(input=None, output=None
                       input_encoding='UTF-8', output_encoding='UTF-8',
                       format='txt', exclude=None)

# perform a conversion for a string and process the result data generator
[p for p in converter.convert("干了吧")]  # [StsDictConv(key=['干', '了'], values=['幹了', '乾了']), '吧']
```


## Configuration 配置

如要自訂轉換方案，可參見[配置檔及詞典檔規格說明](https://github.com/danny0838/sts-lib/blob/master/CONFIG.md)。


## 線上版

[簡繁祕書線上版](https://danny0838.github.io/sts-lib/)

本線上轉換工具支援文字轉換及檔案轉換。前者只要在輸入區填入文字，就會自動轉換並且可以互動式校訂。後者可以用按鈕或拖放選擇一或多個檔案，就會逐一轉換後自動下載。預設檔案輸入輸出編碼皆是UTF-8，如要輸入其他編碼的檔案，可在進階選項設定。

目前內建 [OpenCC](https://github.com/BYVoid/OpenCC)、[MediaWiki](https://github.com/wikimedia/mediawiki)、[新同文堂](https://github.com/tongwentang/tongwen-dict)的轉換方案，並且修正了 OpenCC 演算法缺陷導致一些地區詞無法正常轉換的問題（詳見[相關問題回報](https://github.com/BYVoid/OpenCC/issues/475)）。


## License 許可協議

本專案以 Apache License 2.0 協議授權使用。

詞典檔原始資料來自同文堂、維基百科、OpenCC 等開源專案，再按本專案之需求編校。
