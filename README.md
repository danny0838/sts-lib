# STS 簡繁祕書

STS (Simplified-Traditional Secretary) is an open library for simplified-traditional Chinese text conversion.

簡繁祕書是開源、輕巧的漢字簡繁及地區詞轉換工具。

## Features 特色

* 使用與 [OpenCC](https://github.com/BYVoid/OpenCC) 格式相容的詞典檔。
* 可用「並聯」與「串聯」方式組合多個詞典檔作為轉換方案。
* 可將轉換方案預先編譯為單一詞典檔供本工具或其他程式使用，包括純文字與 JSON 規格，也支援效能較佳的前綴樹格式。
* 支援一對多轉換，轉換結果可輸出為純文字、HTML、JSON 等規格。
* 支援 Unicode 組合字，例如「⿰虫鬼」視為一個字，轉換時不會因為詞典有「虫=>蟲」而被轉為「⿰蟲鬼」。
* 簡繁對應、異體字對應、地區慣用詞對應等不同的對應關係皆區分至不同的詞典檔。
* 詞典及配置檔與程式本體分離，可自由修改、擴充。

## Usage 使用

### Installation 安裝

    pip install -U sts-lib

### Command Line

* `sts --help` 或 `sts COMMAND --help` 檢視可用指令的詳細說明文檔。

* `sts convert [-c CONFIG] [-i INPUT] [-o OUTPUT] [-f FORMAT] [--mark] [--exclude PATTERN]` 執行簡繁轉換：
  * `CONFIG` 為內建配置檔名稱或自製 JSON 配置檔的路徑。可用的內建配置檔詳見 [sts/data/config](https://github.com/danny0838/sts-lib/tree/master/sts/data/config) 目錄，可簡寫，例如輸入 `s2t` 代表使用 `sts/data/config/s2t.json`。
  * `INPUT` 為欲轉換的檔案（省略時讀取標準輸入 stdin）。
  * `OUTPUT` 為欲輸出的檔案（省略時輸出至標準輸出 stdout）。
  * `FORMAT` 指定輸出格式，可用格式如下：
    * `txt`：純文字，適合一般使用。可加上 `--mark` 參數標示轉換過的文字
    * `html`：加上 HTML 標記的文本，可嵌入至網頁應用程式做互動式校對。
    * `htmlpage`：加入 HTML 樣式的網頁，可直接開啟做互動式校對。
    * `json`：以 JSON 格式表示轉換輸出，可用其他程式進一步解析處理。
  * `PATTERN` 指定用於忽略簡繁轉換的正規表示式。有指定 `return` 子群組時會取代為子群組的值。
    * 例如 `sts convert -c s2twp --exclude "「.*?」"` 會把 `「程序」正义` 轉換為 `「程序」正義`。
    * 例如 `sts convert -c s2twp --exclude "-{(?P<return>.*?)}-"` 會把 `-{程序}-正义` 轉換為 `程序正義`。

### Python

```python
from sts import StsListMaker, StsConverter

# generate a dictionary file from a config and get its path
dictfile = StsListMaker().make('s2t', quiet=True)

# initialize the converter from the dictionary file
converter = StsConverter(dictfile, options={})

# perform conversion for a text
converter.convert_text('汉字')  # 漢字

# perform conversion for a file (None for stdin/stdout)
converter.convert_file(input=None, output=None)

# process converted data stream
[p for p in converter.convert("汉字")]  # [StsDictConv(key='汉', values=['漢']), '字']
```

## License 許可協議

本專案以 Apache License 2.0 協議授權使用。

詞典檔原始資料來自同文堂、維基百科、OpenCC 等開源專案，再按本專案之需求編校。
