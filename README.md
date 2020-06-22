# STS 簡繁祕書

STS (Simplified-Traditional Secretary) is an open library for simplified-traditional Chinese text conversion.

簡繁祕書是開源、輕巧的漢字簡繁及地區詞轉換工具。

## Features 特色

* 可用「並聯」與「串聯」方式組合多個詞典檔作為轉換方案。
* 可將轉換方案預先編譯為單一詞典檔供本工具或其他程式使用，包括純文字與 JSON 規格，也支援效能較佳的前綴樹格式。
* 支援一對多轉換，轉換結果可輸出為純文字、HTML、JSON 等規格。
* 支援 Unicode 組合字元，例如「⿰虫鬼」會視為一個字，轉換時不會因為詞典有「虫=>鬼」而被轉為「⿰蟲鬼」。
* 簡繁對應、異體字對應、地區慣用詞對應等不同的對應關係皆區分至不同的詞典檔。
* 詞典及配置檔與程式本體分離，可自由修改、擴充。

## Usage 使用

### Installation 安裝

    pip install -U sts-lib

### Commands 命令

#### 轉換文本

    sts convert [-c CONFIG] [-i INPUT] [-o OUTPUT] [-f FORMAT]

其中 `CONFIG` 為內建或自製 JSON 配置檔的路徑。可用的內建配置檔詳見 `sts/data/config` 目錄，可簡寫，例如輸入 `s2t` 代表使用 `sts/data/config/s2t.json`。

`INPUT` 為欲轉換的檔案（省略則使用標準輸入 stdin），`OUTPUT` 為欲輸出的檔案（省略則輸出至標準輸出 stdout）。

`FORMAT` 可指定輸出格式，包括 `txt` 為純文字（一般使用；可加上 `--mark` 參數標示轉換過的文字），`html` 為加上 HTML 標記的文本（可嵌入至網頁應用程式做互動式校對），`htmlpage` 為加入 HTML 樣式的網頁（可直接開啟做互動式校對），`json` 為轉換好的資料流（可導流至其他程式分析和利用）。

#### 檢視說明文檔

可用 `sts --help` 或 `sts COMMAND --help` 檢視可用指令的詳細說明文檔。

## License 許可協議

本專案以 Apache License 2.0 協議授權使用。

詞典檔原始資料來自同文堂、維基百科、OpenCC 等開源專案，再按本專案之需求編校。
