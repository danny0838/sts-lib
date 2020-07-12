# STS 簡繁祕書

STS (Simplified-Traditional Secretary) is an open library for flexible simplified-traditional Chinese text conversion.

簡繁祕書是開源、輕巧、有彈性的中文簡繁轉換工具，也支援異體字轉換及地區慣用詞轉換。

## Features 特色

* 使用與 [OpenCC](https://github.com/BYVoid/OpenCC) 格式相容的詞典檔。
* 可「並聯」或「串聯」組合多個詞典檔作為轉換方案，並預先儲存成單一詞典檔以加速載入。詞典檔更新時也會自動重新生成組合詞典。
* 簡繁對應、異體字對應、地區慣用詞對應等不同的對應關係皆區分至不同的詞典檔。
* 詞典及配置檔與程式本體分離，可自由修改、擴充。
* 支援一對多轉換，轉換結果可輸出為純文字、HTML、JSON 等格式。
* 支援 Unicode 組合字，例如「⿰虫鬼」視為一個字，不會因為詞典有「虫=>蟲」而被轉為「⿰蟲鬼」。
* 支援用正規表示式略過特定文字的轉換。
* 支援編碼轉換，可自訂輸入及輸出檔案的字元編碼。

## Usage 使用

### Installation 安裝

    pip install -U sts-lib

### Command Line

* `sts --help` 或 `sts COMMAND --help` 檢視可用指令的詳細說明文檔。

* `sts convert [OPTIONs] [file [file ...]]` 執行簡繁轉換：
  * `file` 為一或多個欲轉換的檔案。（省略則讀取標準輸入 STDIN）
  * `-c CONFIG` 指定配置檔，可為內建配置檔名稱或自製 JSON 配置檔的路徑。可用的內建配置檔詳見 [sts/data/config](https://github.com/danny0838/sts-lib/tree/master/sts/data/config) 目錄，可簡寫，例如輸入 `s2t` 代表使用 `sts/data/config/s2t.json`。
  * `-f FORMAT` 指定輸出格式，可用格式如下：
    * `txt`：純文字，適合一般使用。
    * `txtm`：純文字加轉換標示。
    * `html`：加上 HTML 標記的文本，可嵌入至網頁應用程式做互動式校對。
    * `htmlpage`：加入 HTML 樣式的網頁，可直接開啟做互動式校對。
    * `json`：以 JSON 格式表示轉換輸出，可用其他程式進一步解析處理。
  * `--exclude PATTERN` 指定用於忽略簡繁轉換的正規表示式。有指定 `return` 子群組時會取代為子群組的值。
    * 例如 `sts convert -c s2twp --exclude "「.*?」"` 會把 `「程序」正义` 轉換為 `「程序」正義`。
    * 例如 `sts convert -c s2twp --exclude "-{(?P<return>.*?)}-"` 會把 `-{程序}-正义` 轉換為 `程序正義`。
  * `--in-enc ENCODING` 指定輸入編碼。可用編碼參見[這裡](https://docs.python.org/3/library/codecs.html#standard-encodings)。
  * `--out-enc ENCODING` 指定輸出編碼。可用編碼參見[這裡](https://docs.python.org/3/library/codecs.html#standard-encodings)。
  * `-o OUTPUT` 指定對應輸入檔案轉換結果的輸出路徑。（無對應者輸出至原處）
  * `--stdout` 將所有轉換結果輸出至標準輸出 STDOUT。

### Python

```python
from sts import StsMaker, StsConverter

# generate a dictionary file from a config and get its path
dictfile = StsMaker().make('s2t', quiet=True)

# initialize the converter from the dictionary file
converter = StsConverter(dictfile, options={})

# perform conversion for a text
converter.convert_text('汉字')  # 漢字

# perform conversion for a file (None for stdin/stdout)
converter.convert_file(input=None, output=None)

# process converted data stream
[p for p in converter.convert("汉字")]  # [StsDictConv(key=['汉'], values=['漢']), '字']
```

## License 許可協議

本專案以 Apache License 2.0 協議授權使用。

詞典檔原始資料來自同文堂、維基百科、OpenCC 等開源專案，再按本專案之需求編校。
