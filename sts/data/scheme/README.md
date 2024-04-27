# 字體規範表

除非另有聲明，以下「正體字」或「繁體字」指本專案定義的標準字體，「簡化字」指中國大陸標準的簡化字。

本專案整理正體字採「能分則不合」原則——當兩個字的字義有別，則二者皆視為正體字。例如「著」、「着」在臺灣標準皆使用「著」，但二者字義有別，因而皆列為正體字。

正體字之間原則上不做轉換，除非在與特定地區轉換時為適應當地標準而不得不為。

## [`traditional.tsv`](./traditional.tsv) - 正體字表

此表列出本專案定義的所有正體字，及其對應之異體字與各地區標準。

「異體字」的意義集合應與正體字相等，否則應另收為正體字。

一般而言，[Unicode標準](https://www.unicode.org/reports/tr38/index.html#N10211)中有 kZVariant 標記的字，皆可收錄為異體字；有 kSemanticVariant 和 kSpecializedSemanticVariant 標記的字亦可考慮收錄。

| 正體字 | 異體字 | 中國標準 | 臺灣標準 | 香港標準 | 日本標準 | 日本舊字體 | 附註 |
|--------|--------|----------|----------|----------|----------|------------|------|

## [`ts_multi.tsv`](./ts_multi.tsv) - 正簡一對多轉換表

| 正體字 | 簡化字 | 說明 | 例詞 |
|--------|--------|------|------|

## [`st_multi.tsv`](./st_multi.tsv) - 簡正一對多轉換表

| 簡化字 | 正體字 | 說明 | 例詞 |
|--------|--------|------|------|