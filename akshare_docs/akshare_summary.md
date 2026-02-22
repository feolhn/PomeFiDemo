# Docs

## README

**资源分享**：对于想了解更多财经数据与量化投研的小伙伴，推荐一个专注于财经数据和量化研究的知识社区。
该社区提供相关文档和视频学习资源，汇集了各类财经数据源和量化投研工具的使用经验。
有兴趣深入学习的朋友可点此[了解更多](https://t.zsxq.com/ZCxUG)，也推荐大家关注微信公众号【数据科学实战】。

## Overview

[AKShare](https://github.com/akfamily/akshare) requires Python(64 bit) 3.9 or higher and
aims to simplify the process of fetching financial data.

**Write less, get more!**

- Documentation: [中文文档](https://akshare.akfamily.xyz/)

## Installation

### General

```shell
pip install akshare --upgrade
```

### China

```shell
pip install akshare -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com  --upgrade
```

### PR

Please check out [Documentation](https://akshare.akfamily.xyz/contributing.html) if you
want to contribute to AKShare

### Docker

#### Pull images

```shell
docker pull registry.cn-shanghai.aliyuncs.com/akfamily/aktools:jupyter
```

#### Run Container

```shell
docker run -it registry.cn-shanghai.aliyuncs.com/akfamily/aktools:jupyter python
```

#### Test

```python
import akshare as ak

print(ak.__version__)
```

## Usage

### Data

Code:

```python
import akshare as ak

stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20170301", end_date='20231022', adjust="")
print(stock_zh_a_hist_df)
```

Output:

```
      日期          开盘   收盘    最高  ...  振幅   涨跌幅  涨跌额  换手率
0     2017-03-01   9.49   9.49   9.55  ...  0.84  0.11  0.01  0.21
1     2017-03-02   9.51   9.43   9.54  ...  1.26 -0.63 -0.06  0.24
2     2017-03-03   9.41   9.40   9.43  ...  0.74 -0.32 -0.03  0.20
3     2017-03-06   9.40   9.45   9.46  ...  0.74  0.53  0.05  0.24
4     2017-03-07   9.44   9.45   9.46  ...  0.63  0.00  0.00  0.17
          ...    ...    ...    ...  ...   ...   ...   ...   ...
1610  2023-10-16  11.00  11.01  11.03  ...  0.73  0.09  0.01  0.26
1611  2023-10-17  11.01  11.02  11.05  ...  0.82  0.09  0.01  0.25
1612  2023-10-18  10.99  10.95  11.02  ...  1.00 -0.64 -0.07  0.34
1613  2023-10-19  10.91  10.60  10.92  ...  3.01 -3.20 -0.35  0.61
1614  2023-10-20  10.55  10.60  10.67  ...  1.51  0.00  0.00  0.27
[1615 rows x 11 columns]
```

### Plot

Code:

```python
import akshare as ak
import mplfinance as mpf  # Please install mplfinance as follows: pip install mplfinance

stock_us_daily_df = ak.stock_us_daily(symbol="AAPL", adjust="qfq")
stock_us_daily_df = stock_us_daily_df.set_index(["date"])
stock_us_daily_df = stock_us_daily_df["2020-04-01": "2020-04-29"]
mpf.plot(stock_us_daily_df, type="candle", mav=(3, 6, 9), volume=True, show_nontrading=False)
```

Output:

![KLine](https://jfds-1252952517.cos.ap-chengdu.myqcloud.com/akshare/readme/home/AAPL_candle.png)

## Features

- **Easy of use**: Just one line code to fetch the data;
- **Extensible**: Easy to customize your own code with other application;
- **Powerful**: Python ecosystem.

## Tutorials

1. [Overview](https://akshare.akfamily.xyz/introduction.html)
2. [Installation](https://akshare.akfamily.xyz/installation.html)
3. [Tutorial](https://akshare.akfamily.xyz/tutorial.html)
4. [Data Dict](https://akshare.akfamily.xyz/data/index.html)
5. [Subjects](https://akshare.akfamily.xyz/topic/index.html)

## Contribution

[AKShare](https://github.com/akfamily/akshare) is still under developing, feel free to open issues and pull requests:

- Report or fix bugs
- Require or publish interface
- Write or fix documentation
- Add test cases

> Notice: We use [Ruff](https://github.com/astral-sh/ruff) to format the code

## Statement

1. All data provided by [AKShare](https://github.com/akfamily/akshare) is just for academic research purpose;
2. The data provided by [AKShare](https://github.com/akfamily/akshare) is for reference only and does not constitute any investment proposal;
3. Any investor based on [AKShare](https://github.com/akfamily/akshare) research should pay more attention to data risk;
4. [AKShare](https://github.com/akfamily/akshare) will insist on providing open-source financial data;
5. Based on some uncontrollable factors, some data interfaces in [AKShare](https://github.com/akfamily/akshare) may be removed;
6. Please follow the relevant open-source protocol used by [AKShare](https://github.com/akfamily/akshare);
7. Provide HTTP API for the person who uses other program language: [AKTools](https://aktools.readthedocs.io/).

## Show your style

Use the badge in your project's README.md:

```markdown
[![Data: akshare](https://img.shields.io/badge/Data%20Science-AKShare-green)](https://github.com/akfamily/akshare)
```

Using the badge in README.rst:

```
.. image:: https://img.shields.io/badge/Data%20Science-AKShare-green
    :target: https://github.com/akfamily/akshare
```

Looks like this:

[![Data: akshare](https://img.shields.io/badge/Data%20Science-AKShare-green)](https://github.com/akfamily/akshare)

## Citation

Please use this **bibtex** if you want to cite this repository in your publications:

```markdown
@misc{akshare,
    author = {Albert King and Yaojie Zhang},
    title = {AKShare},
    year = {2022},
    publisher = {GitHub},
    journal = {GitHub repository},
    howpublished = {\url{https://github.com/akfamily/akshare}},
}
```

## [AKShare](https://github.com/akfamily/akshare) 股票数据

### A股

#### 个股信息查询-东财

接口: stock_individual_info_em

目标地址: http://quote.eastmoney.com/concept/sh603777.html?from=classic

描述: 东方财富-个股-股票信息

限量: 单次返回指定 symbol 的个股信息

输入参数

| 名称      | 类型    | 描述                      |
|---------|-------|-------------------------|
| symbol  | str   | symbol="603777"; 股票代码   |
| timeout | float | timeout=None; 默认不设置超时参数 |

输出参数

| 名称    | 类型     | 描述  |
|-------|--------|-----|
| item  | object | -   |
| value | object | -   |

接口示例

```python
import akshare as ak

stock_individual_info_em_df = ak.stock_individual_info_em(symbol="000001")
print(stock_individual_info_em_df)
```

数据示例

```
   item               value
0    最新               7.05
1  股票代码             000002
2  股票简称            万  科Ａ
3   总股本       11930709471.0
4   流通股        9716935865.0
5   总市值  84111501770.550003
6  流通市值      68504397848.25
7    行业              房地产开发
8  上市时间            19910129
```

#### 实时行情数据

##### 实时行情数据-东财

###### 沪深京 A 股

接口: stock_zh_a_spot_em

目标地址: https://quote.eastmoney.com/center/gridlist.html#hs_a_board

描述: 东方财富网-沪深京 A 股-实时行情数据

限量: 单次返回所有沪深京 A 股上市公司的实时行情数据

输入参数

| 名称  | 类型  | 描述  |
|-----|-----|-----|
| -   | -   | -   |

输出参数

| 名称      | 类型      | 描述      |
|---------|---------|---------|
| 序号      | int64   | -       |
| 代码      | object  | -       |
| 名称      | object  | -       |
| 最新价     | float64 | -       |
| 涨跌幅     | float64 | 注意单位: % |
| 涨跌额     | float64 | -       |
| 成交量     | float64 | 注意单位: 手 |
| 成交额     | float64 | 注意单位: 元 |
| 振幅      | float64 | 注意单位: % |
| 最高      | float64 | -       |
| 最低      | float64 | -       |
| 今开      | float64 | -       |
| 昨收      | float64 | -       |
| 量比      | float64 | -       |
| 换手率     | float64 | 注意单位: % |
| 市盈率-动态  | float64 | -       |
| 市净率     | float64 | -       |
| 总市值     | float64 | 注意单位: 元 |
| 流通市值    | float64 | 注意单位: 元 |
| 涨速      | float64 | -       |
| 5分钟涨跌   | float64 | 注意单位: % |
| 60日涨跌幅  | float64 | 注意单位: % |
| 年初至今涨跌幅 | float64 | 注意单位: % |

接口示例

```python
import akshare as ak

stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
print(stock_zh_a_spot_em_df)
```

数据示例

```
        序号 代码    名称    最新价  ...   涨速 5分钟涨跌  60日涨跌幅  年初至今涨跌幅
0        1  836149  旭杰科技   7.31  ...  0.00   0.00   28.47    -9.53
1        2  300767  震安科技   9.28  ...  0.00   0.00   -9.55   -46.61
2        3  300125  ST聆达   4.67  ...  0.00   0.00  177.98   -62.97
3        4  301027  华蓝集团   8.93  ...  0.00   0.00   17.81   -28.56
4        5  300584  海辰药业  23.26  ...  0.00   0.00   42.44     0.13
...    ...     ...   ...    ...  ...   ...    ...     ...      ...
5630  5631  300531   优博讯  12.45  ... -0.16  -0.24   25.50   -18.52
5631  5632  301302  华如科技  13.47  ...  0.07  -0.07  -28.88   -46.36
5632  5633  300496  中科创达  32.30  ... -0.09  -0.12  -44.60   -59.53
5633  5634  300050  世纪鼎利   5.04  ... -0.20   0.60   72.01     6.55
5634  5635  832175  东方碳素   6.48  ...  0.00   0.00  -21.64   -47.57
[5635 rows x 23 columns]
```

##### 实时行情数据-雪球

接口: stock_individual_spot_xq

目标地址: https://xueqiu.com/S/SH513520

描述: 雪球-行情中心-个股

限量: 单次获取指定 symbol 的最新行情数据

输入参数

| 名称      | 类型    | 描述                                                             |
|---------|-------|----------------------------------------------------------------|
| symbol  | str   | symbol="SH600000"; 证券代码，可以是 A 股个股代码，A 股场内基金代码，A 股指数，美股代码, 美股指数 |
| token   | float | token=None; 默认不设置token                                         |
| timeout | float | timeout=None; 默认不设置超时参数                                        |

输出参数

| 名称    | 类型     | 描述 |
|-------|--------|----|
| item  | object | -  |
| value | object | -  |

接口示例

```python
import akshare as ak

stock_individual_spot_xq_df = ak.stock_individual_spot_xq(symbol="SH600000")
print(stock_individual_spot_xq_df)
```

数据示例

```
        item                value
0         代码             SH600000
1      52周最高                11.02
2        流通股          29352178996
3         跌停                 8.69
4         最高                10.29
5        流通值       299392225759.0
6     最小交易单位                  100
7         涨跌                 0.55
8       每股收益                 1.54
9         昨收                 9.65
10       成交量            149422915
11       周转率                 0.51
12     52周最低               6.8673
13        名称                 浦发银行
14       交易所                   SH
15    市盈率(动)                6.615
16  基金份额/总股本          29352178996
17   净资产中的商誉             0.726713
18        均价               10.048
19        涨幅                  5.7
20        振幅                  5.6
21        现价                 10.2
22    今年以来涨幅                -0.87
23      发行日期  1999-11-10 00:00:00
24        最低                 9.75
25  资产净值/总市值       299392225759.0
26   股息(TTM)                0.321
27  股息率(TTM)                3.147
28        货币                  CNY
29     每股净资产                22.36
30    市盈率(静)                6.615
31       成交额         1501459278.0
32       市净率                0.456
33        涨停                10.62
34  市盈率(TTM)                6.615
35        时间  2025-04-08 15:00:00
36        今开                 9.77
```


#### 历史行情数据

##### 历史行情数据-东财

接口: stock_zh_a_hist

目标地址: https://quote.eastmoney.com/concept/sh603777.html?from=classic(示例)

描述: 东方财富-沪深京 A 股日频率数据; 历史数据按日频率更新, 当日收盘价请在收盘后获取

限量: 单次返回指定沪深京 A 股上市公司、指定周期和指定日期间的历史行情日频率数据

输入参数

| 名称         | 类型    | 描述                                                       |
|------------|-------|----------------------------------------------------------|
| symbol     | str   | symbol='603777'; 股票代码可以在 **ak.stock_zh_a_spot_em()** 中获取 |
| period     | str   | period='daily'; choice of {'daily', 'weekly', 'monthly'} |
| start_date | str   | start_date='20210301'; 开始查询的日期                           |
| end_date   | str   | end_date='20210616'; 结束查询的日期                             |
| adjust     | str   | 默认返回不复权的数据; qfq: 返回前复权后的数据; hfq: 返回后复权后的数据               |
| timeout    | float | timeout=None; 默认不设置超时参数                                  |

**股票数据复权**

1. 为何要复权：由于股票存在配股、分拆、合并和发放股息等事件，会导致股价出现较大的缺口。
若使用不复权的价格处理数据、计算各种指标，将会导致它们失去连续性，且使用不复权价格计算收益也会出现错误。
为了保证数据连贯性，常通过前复权和后复权对价格序列进行调整。

2. 前复权：保持当前价格不变，将历史价格进行增减，从而使股价连续。
前复权用来看盘非常方便，能一眼看出股价的历史走势，叠加各种技术指标也比较顺畅，是各种行情软件默认的复权方式。
这种方法虽然很常见，但也有两个缺陷需要注意。

    2.1 为了保证当前价格不变，每次股票除权除息，均需要重新调整历史价格，因此其历史价格是时变的。
这会导致在不同时点看到的历史前复权价可能出现差异。

    2.2 对于有持续分红的公司来说，前复权价可能出现负值。

3. 后复权：保证历史价格不变，在每次股票权益事件发生后，调整当前的股票价格。
后复权价格和真实股票价格可能差别较大，不适合用来看盘。
其优点在于，可以被看作投资者的长期财富增长曲线，反映投资者的真实收益率情况。

4. 在量化投资研究中普遍采用后复权数据。

输出参数-历史行情数据

| 名称   | 类型      | 描述          |
|------|---------|-------------|
| 日期   | object  | 交易日         |
| 股票代码 | object  | 不带市场标识的股票代码 |
| 开盘   | float64 | 开盘价         |
| 收盘   | float64 | 收盘价         |
| 最高   | float64 | 最高价         |
| 最低   | float64 | 最低价         |
| 成交量  | int64   | 注意单位: 手     |
| 成交额  | float64 | 注意单位: 元     |
| 振幅   | float64 | 注意单位: %     |
| 涨跌幅  | float64 | 注意单位: %     |
| 涨跌额  | float64 | 注意单位: 元     |
| 换手率  | float64 | 注意单位: %     |

接口示例-历史行情数据-后复权

```python
import akshare as ak

stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20170301", end_date='20240528', adjust="hfq")
print(stock_zh_a_hist_df)
```

数据示例-历史行情数据-后复权

```
           日期    股票代码   开盘     收盘  ...    振幅   涨跌幅   涨跌额 换手率
0     2017-03-01  000001  1575.20  1575.20  ...  0.83  0.10   1.63  0.21
1     2017-03-02  000001  1578.45  1565.45  ...  1.24 -0.62  -9.75  0.24
2     2017-03-03  000001  1562.20  1560.57  ...  0.73 -0.31  -4.88  0.20
3     2017-03-06  000001  1560.57  1568.70  ...  0.73  0.52   8.13  0.24
4     2017-03-07  000001  1567.07  1568.70  ...  0.62  0.00   0.00  0.17
...          ...     ...      ...      ...  ...   ...   ...    ...   ...
1755  2024-05-22  000001  2131.04  2131.04  ...  2.14  0.08   1.62  1.09
1756  2024-05-23  000001  2126.17  2105.04  ...  1.68 -1.22 -26.00  0.95
1757  2024-05-24  000001  2100.16  2090.41  ...  1.47 -0.69 -14.63  0.72
1758  2024-05-27  000001  2090.41  2122.92  ...  1.71  1.56  32.51  0.75
1759  2024-05-28  000001  2121.29  2105.04  ...  1.68 -0.84 -17.88  0.62
[1760 rows x 12 columns]
```
#### 同行比较

##### 成长性比较

接口: stock_zh_growth_comparison_em

目标地址: https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?type=web&code=000895&color=b#/thbj/czxbj

描述: 东方财富-行情中心-同行比较-成长性比较

限量: 单次返回全部数据

输入参数

| 名称         | 类型  | 描述                    |
|------------|-----|-----------------------|
| symbol     | str | symbol="SZ000895"     |

输出参数

| 名称               | 类型      | 描述 |
|------------------|---------|----|
| 代码               | object  | -  |
| 简称               | object  | -  |
| 基本每股收益增长率-3年复合   | float64 | -  |
| 基本每股收益增长率-24A    | float64 | -  |
| 基本每股收益增长率-TTM    | float64 | -  |
| 基本每股收益增长率-25E    | float64 | -  |
| 基本每股收益增长率-26E    | float64 | -  |
| 基本每股收益增长率-27E    | float64 | -  |
| 营业收入增长率-3年复合     | float64 | -  |
| 营业收入增长率-24A      | float64 | -  |
| 营业收入增长率-TTM      | float64 | -  |
| 营业收入增长率-25E      | float64 | -  |
| 营业收入增长率-26E      | float64 | -  |
| 营业收入增长率-27E      | float64 | -  |
| 净利润增长率-3年复合      | float64 | -  |
| 净利润增长率-24A       | float64 | -  |
| 净利润增长率-TTM       | float64 | -  |
| 净利润增长率-25E       | float64 | -  |
| 净利润增长率-26E       | float64 | -  |
| 净利润增长率-27E       | float64 | -  |
| 基本每股收益增长率-3年复合排名 | float64 | -  |

接口示例

```python
import akshare as ak

stock_zh_growth_comparison_em_df = ak.stock_zh_growth_comparison_em(symbol="SZ000895")
print(stock_zh_growth_comparison_em_df)
```

数据示例

```
       代码    简称  基本每股收益增长率-3年复合  ...  净利润增长率-26E  净利润增长率-27E  基本每股收益增长率-3年复合排名
0    行业中值  行业中值       -8.790000  ...   21.290000   16.135000               NaN
1    行业平均  行业平均      -31.127395  ...   57.622875   18.847125               NaN
2  600530  交大昂立       81.710000  ...         NaN         NaN               1.0
3  600186  莲花控股       58.740000  ...   28.700000   22.480000               2.0
4  600962  国投中鲁       51.860000  ...         NaN         NaN               3.0
5  600737  中粮糖业       48.850000  ...   39.030000   22.690000               4.0
6  003000  劲仔食品       46.100000  ...   22.070000   17.520000               5.0
7  000895  双汇发展        0.840000  ...    4.320000    3.980000              38.0
[8 rows x 21 columns]
```

##### 估值比较

接口: stock_zh_valuation_comparison_em

目标地址: https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?type=web&code=000895&color=b#/thbj/gzbj

描述: 东方财富-行情中心-同行比较-估值比较

限量: 单次返回全部数据

输入参数

| 名称         | 类型  | 描述                    |
|------------|-----|-----------------------|
| symbol     | str | symbol="SZ000895"     |

输出参数

| 名称            | 类型      | 描述 |
|---------------|---------|----|
| 排名            | object  | -  |
| 代码            | object  | -  |
| 简称            | object  | -  |
| PEG           | float64 | -  |
| 市盈率-24A       | float64 | -  |
| 市盈率-TTM       | float64 | -  |
| 市盈率-25E       | float64 | -  |
| 市盈率-26E       | float64 | -  |
| 市盈率-27E       | float64 | -  |
| 市销率-24A       | float64 | -  |
| 市销率-TTM       | float64 | -  |
| 市销率-25E       | float64 | -  |
| 市销率-26E       | float64 | -  |
| 市销率-27E       | float64 | -  |
| 市净率-24A       | float64 | -  |
| 市净率-MRQ       | float64 | -  |
| 市现率1-24A      | float64 | -  |
| 市现率1-TTM      | float64 | -  |
| 市现率2-24A      | float64 | -  |
| 市现率2-TTM      | float64 | -  |
| EV/EBITDA-24A | float64 | -  |

接口示例

```python
import akshare as ak

stock_zh_valuation_comparison_em_df = ak.stock_zh_valuation_comparison_em(symbol="SZ000895")
print(stock_zh_valuation_comparison_em_df)
```

数据示例

```
         排名      代码    简称  ...     市现率2-24A     市现率2-TTM  EV/EBITDA-24A
0  42.0/120  000895  双汇发展  ...    29.790457 -1045.264127      12.503574
1       nan    行业平均  行业平均  ...  1036.299305   -81.550319      12.794686
2       nan    行业中值  行业中值  ...   -11.801449   -13.610393      18.565517
3       1.0  920786  骑士乳业  ...   -10.676185   -23.320786      14.613055
4       2.0  002852   道道全  ...    94.382638   -14.822839      10.933433
5       3.0  002840  华统股份  ...   -62.597528    39.150932      19.671557
6       4.0  605077  华康股份  ...    -2.588921   -50.802629      15.723042
7       5.0  002286   保龄宝  ...   257.860564  -114.930447      12.453163
[8 rows x 20 columns]
```

##### 杜邦分析比较

接口: stock_zh_dupont_comparison_em

目标地址: https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?type=web&code=000895&color=b#/thbj/dbfxbj

描述: 东方财富-行情中心-同行比较-杜邦分析比较

限量: 单次返回全部数据

输入参数

| 名称         | 类型  | 描述                    |
|------------|-----|-----------------------|
| symbol     | str | symbol="SZ000895"     |

输出参数

| 名称          | 类型      | 描述 |
|-------------|---------|----|
| 代码          | object  | -  |
| 简称          | object  | -  |
| ROE-3年平均    | float64 | -  |
| ROE-22A     | float64 | -  |
| ROE-23A     | float64 | -  |
| ROE-24A     | float64 | -  |
| 净利率-3年平均    | float64 | -  |
| 净利率-22A     | float64 | -  |
| 净利率-23A     | float64 | -  |
| 净利率-24A     | float64 | -  |
| 总资产周转率-3年平均 | float64 | -  |
| 总资产周转率-22A  | float64 | -  |
| 总资产周转率-23A  | float64 | -  |
| 总资产周转率-24A  | float64 | -  |
| 权益乘数-3年平均   | float64 | -  |
| 权益乘数-22A    | float64 | -  |
| 权益乘数-23A    | float64 | -  |
| 权益乘数-24A    | float64 | -  |
| ROE-3年平均排名  | float64 | -  |


接口示例

```python
import akshare as ak

stock_zh_dupont_comparison_em_df = ak.stock_zh_dupont_comparison_em(symbol="SZ000895")
print(stock_zh_dupont_comparison_em_df)
```

数据示例

```
    代码    简称  ROE-3年平均  ROE-22A  ...  权益乘数-22A  权益乘数-23A  权益乘数-24A  ROE-3年平均排名
0    行业平均  行业平均      5.70     5.51  ...    191.76    189.10   185.080         NaN
1    行业中值  行业中值      7.71     7.89  ...    149.35    142.50   143.105         NaN
2  605499  东鹏饮料     38.09    30.97  ...    234.37    232.62   294.820         1.0
3  002847  盐津铺子     36.48    30.03  ...    213.82    196.34   203.650         2.0
4  000895  双汇发展     24.21    25.17  ...    164.15    173.44   174.840         3.0
5  603262  技源集团     24.02    28.06  ...    152.21    132.11   125.360         4.0
6  603288  海天味业     22.24    24.89  ...    126.69    132.34   130.110         5.0
7  000848  承德露露     21.92    23.53  ...    136.51    133.85   133.510         6.0
[8 rows x 19 columns]
```

##### 公司规模

接口: stock_zh_scale_comparison_em

目标地址: https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?type=web&code=000895&color=b#/thbj/gsgm

描述: 东方财富-行情中心-同行比较-公司规模

限量: 单次返回全部数据

输入参数

| 名称         | 类型  | 描述                    |
|------------|-----|-----------------------|
| symbol     | str | symbol="SZ000895"     |

输出参数

| 名称     | 类型      | 描述 |
|--------|---------|----|
| 代码     | object  | -  |
| 简称     | object  | -  |
| 总市值    | float64 | -  |
| 总市值排名  | int64   | -  |
| 流通市值   | float64 | -  |
| 流通市值排名 | int64   | -  |
| 营业收入   | float64 | -  |
| 营业收入排名 | int64   | -  |
| 净利润    | float64 | -  |
| 净利润排名  | int64   | -  |

接口示例

```python
import akshare as ak

stock_zh_scale_comparison_em_df = ak.stock_zh_scale_comparison_em(symbol="SZ000895")
print(stock_zh_scale_comparison_em_df)
```

数据示例

```
       代码    简称           总市值  总市值排名    流通市值  流通市值排名          营业收入  营业收入排名           净利润  净利润排名
0  000895  双汇发展  8.685906e+10      5  868.48       4  2.850309e+10       3  2.351218e+09      4
```


### 美股

#### 实时行情数据-东财

接口: stock_us_spot_em

目标地址: https://quote.eastmoney.com/center/gridlist.html#us_stocks

描述: 东方财富网-美股-实时行情

限量: 单次返回美股所有上市公司的实时行情数据

输入参数

| 名称  | 类型  | 描述  |
|-----|-----|-----|
| -   | -   | -   |

输出参数

| 名称  | 类型      | 描述              |
|-----|---------|-----------------|
| 序号  | int64   | -               |
| 名称  | object  | -               |
| 最新价 | float64 | 注意单位: 美元        |
| 涨跌额 | float64 | 注意单位: 美元        |
| 涨跌幅 | float64 | 注意单位: %         |
| 开盘价 | float64 | 注意单位: 美元        |
| 最高价 | float64 | 注意单位: 美元        |
| 最低价 | float64 | 注意单位: 美元        |
| 昨收价 | float64 | 注意单位: 美元        |
| 总市值 | float64 | 注意单位: 美元        |
| 市盈率 | float64 | -               |
| 成交量 | float64 | -               |
| 成交额 | float64 | 注意单位: 美元        |
| 振幅  | float64 | 注意单位: %         |
| 换手率 | float64 | 注意单位: %         |
| 代码  | object  | 注意: 用来获取历史数据的代码 |

接口示例

```python
import akshare as ak

stock_us_spot_em_df = ak.stock_us_spot_em()
print(stock_us_spot_em_df)
```

数据示例

```
          序号                         名称  ...      换手率         代码
0          1        Nexalin Technology Inc Wt  ...      NaN  105.NXLIW
1          2           Bionexus Gene Lab Corp  ...   427.44   105.BGLC
2          3  PepperLime Health Acquisition C  ...      NaN  105.PEPLW
3          4  Alliance Entertainment Holding   ...      NaN  105.AENTW
4          5         Digital Brands Group Inc  ...  6569.86   105.DBGI
      ...                              ...  ...      ...        ...
11616  11617                      BIOLASE Inc  ...   582.75   105.BIOL
11617  11618           Sunshine Biopharma Inc  ...   144.85   105.SBFM
11618  11619                      Sientra Inc  ...    42.00   105.SIEN
11619  11620        Sunshine Biopharma Inc Wt  ...      NaN  105.SBFMW
11620  11621  Social Leverage Acquisition Cor  ...      NaN  105.SLACW
[11621 rows x 16 columns]
```
### 港股

#### 实时行情数据-东财

接口: stock_hk_spot_em

目标地址: http://quote.eastmoney.com/center/gridlist.html#hk_stocks

描述: 所有港股的实时行情数据; 该数据有 15 分钟延时

限量: 单次返回最近交易日的所有港股的数据

输入参数

| 名称  | 类型  | 描述  |
|-----|-----|-----|
| -   | -   | -   |

输出参数

| 名称  | 类型      | 描述       |
|-----|---------|----------|
| 序号  | int64   | -        |
| 代码  | object  | -        |
| 名称  | object  | -        |
| 最新价 | float64 | 注意单位: 港元 |
| 涨跌额 | float64 | 注意单位: 港元 |
| 涨跌幅 | float64 | 注意单位: %  |
| 今开  | float64 | -        |
| 最高  | float64 | -        |
| 最低  | float64 | -        |
| 昨收  | float64 | -        |
| 成交量 | float64 | 注意单位: 股  |
| 成交额 | float64 | 注意单位: 港元 |

接口示例

```python
import akshare as ak

stock_hk_spot_em_df = ak.stock_hk_spot_em()
print(stock_hk_spot_em_df)
```

数据示例

```
     序号     代码      名称    最新价  ...    最低   昨收  成交量         成交额
0        1  00593     梦东方   2.62  ...    1.6   1.51   2582500   7104955.0
1        2  08367    倩碧控股  0.225  ...  0.153  0.152  82770000  17723337.0
2        3  03886  康健国际医疗  0.395  ...  0.305   0.29  54347051  19867777.0
3        4  00205    财讯传媒  0.475  ...  0.305   0.35   6920400   3218611.0
4        5  08166  中国农业生态  0.047  ...   0.04  0.037    120000      5230.0
    ...    ...     ...    ...  ...    ...    ...       ...         ...
4523  4524  01335    顺泰控股  0.161  ...  0.152  0.195   2310000    376096.0
4524  4525  08088  八零八八投资  0.051  ...   0.05  0.062   1216000     65144.0
4525  4526  00809  大成生化科技  0.205  ...  0.195   0.25   4024000    875026.0
4526  4527  00378    五龙动力  0.012  ...  0.011  0.015  80412000    991172.0
4527  4528  03638    华邦科技  0.099  ...  0.099  0.128    972000    100308.0
```

#### 证券资料

接口: stock_hk_security_profile_em

目标地址: https://emweb.securities.eastmoney.com/PC_HKF10/pages/home/index.html?code=03900&type=web&color=w#/CompanyProfile

描述: 东方财富-港股-证券资料

限量: 单次返回全部数据

输入参数

| 名称     | 类型  | 描述             |
|--------|-----|----------------|
| symbol | str | symbol="03900" |

输出参数

| 名称             | 类型      | 描述 |
|----------------|---------|----|
| 证券代码           | object  | -  |
| 证券简称           | object  | -  |
| 上市日期           | object  | -  |
| 证券类型           | object  | -  |
| 发行价            | float64 | -  |
| 发行量(股)         | int64   | -  |
| 每手股数           | int64   | -  |
| 每股面值           | object  | -  |
| 交易所            | object  | -  |
| 板块             | object  | -  |
| 年结日            | object  | -  |
| ISIN（国际证券识别编码） | object  | -  |
| 是否沪港通标的        | object  | -  |

接口示例

```python
import akshare as ak

stock_hk_security_profile_em_df = ak.stock_hk_security_profile_em(symbol="03900")
print(stock_hk_security_profile_em_df)
```

数据示例

```
       证券代码  证券简称                 上市日期  ... ISIN（国际证券识别编码）  是否沪港通标的  是否深港通标的
0  03900.HK  绿城中国  2006-07-13 00:00:00  ...   KYG4100M1050        是        是
[1 rows x 14 columns]
```

#### 公司资料

接口: stock_hk_company_profile_em

目标地址: https://emweb.securities.eastmoney.com/PC_HKF10/pages/home/index.html?code=03900&type=web&color=w#/CompanyProfile

描述: 东方财富-港股-公司资料

限量: 单次返回全部数据

输入参数

| 名称     | 类型  | 描述             |
|--------|-----|----------------|
| symbol | str | symbol="03900" |

输出参数

| 名称     | 类型     | 描述 |
|--------|--------|----|
| 公司名称   | object | -  |
| 英文名称   | object | -  |
| 注册地    | object | -  |
| 公司成立日期 | object | -  |
| 所属行业   | object | -  |
| 董事长    | object | -  |
| 公司秘书   | object | -  |
| 员工人数   | int64  | -  |
| 办公地址   | object | -  |
| 公司网址   | object | -  |
| E-MAIL | object | -  |
| 年结日    | object | -  |
| 联系电话   | object | -  |
| 核数师    | object | -  |
| 传真     | object | -  |
| 公司介绍   | object | -  |

接口示例

```python
import akshare as ak

stock_hk_company_profile_em_df = ak.stock_hk_company_profile_em(symbol="03900")
print(stock_hk_company_profile_em_df)
```

数据示例

```
         公司名称  ...                                               公司介绍
0  绿城中国控股有限公司  ...      绿城中国控股有限公司(以下简称“绿城中国”)(股票代码03900.HK),1995年...
[1 rows x 17 columns]
```

#### 财务指标

接口: stock_hk_financial_indicator_em

目标地址: https://emweb.securities.eastmoney.com/PC_HKF10/pages/home/index.html?code=03900&type=web&color=w#/CoreReading

描述: 东方财富-港股-核心必读-最新指标

限量: 单次返回全部数据

输入参数

| 名称     | 类型  | 描述             |
|--------|-----|----------------|
| symbol | str | symbol="03900" |

输出参数

| 名称             | 类型     | 描述 |
|----------------|--------|----|
| 基本每股收益(元)      | object | -  |
| 每股净资产(元)       | object | -  |
| 法定股本(股)        | object | -  |
| 每手股            | object | -  |
| 每股股息TTM(港元)    | object | -  |
| 派息比率(%)        | object | -  |
| 已发行股本(股)       | object | -  |
| 已发行股本-H股(股)    | int64  | -  |
| 每股经营现金流(元)     | object | -  |
| 股息率TTM(%)      | object | -  |
| 总市值(港元)        | object | -  |
| 港股市值(港元)       | object | -  |
| 营业总收入          | object | -  |
| 营业总收入滚动环比增长(%) | object | -  |
| 销售净利率(%)       | object | -  |
| 净利润            | object | -  |
| 净利润滚动环比增长(%)   | object | -  |
| 股东权益回报率(%)     | object | -  |
| 市盈率            | object | -  |
| 市净率            | object | -  |
| 总资产回报率(%)      | object | -  |

接口示例

```python
import akshare as ak

stock_hk_financial_indicator_em_df = ak.stock_hk_financial_indicator_em(symbol="03900")
print(stock_hk_financial_indicator_em_df)
```

数据示例

```
   基本每股收益(元)   每股净资产(元)      法定股本(股)  每手股  每股股息TTM(港元)   派息比率(%)    已发行股本(股)  ...  销售净利率(%)        净利润  净利润滚动环比增长(%)  股东权益回报率(%)        市盈率       市净率  总资产回报率(%)
0       0.08  14.006448  10000000000  500        0.328 -322.1807  2539598690  ...  2.270029  209907000   -114.943944    0.583899 -87.240653  0.640675   0.040922
[1 rows x 21 columns]
```

### 主营介绍-同花顺

接口: stock_zyjs_ths

目标地址: https://basic.10jqka.com.cn/new/000066/operate.html

描述: 同花顺-主营介绍

限量: 单次返回所有数据

输入参数

| 名称     | 类型  | 描述              |
|--------|-----|-----------------|
| symbol | str | symbol="000066" |

输出参数

| 名称   | 类型      | 描述      |
|------|---------|---------|
| 股票代码 | object  | -       |
| 主营业务 | object  | -       |
| 产品类型 | object  | -       |
| 产品名称 | object  | -       |
| 经营范围 | object  | -       |

接口示例

```python
import akshare as ak

stock_zyjs_ths_df = ak.stock_zyjs_ths(symbol="000066")
print(stock_zyjs_ths_df)
```

数据示例

```
     股票代码  ...                                               经营范围
0  000066  ...  计算机软件、硬件、终端及其外部设备、网络系统及系统集成、电子产品及零部件、金融机具、税控机具...
[1 rows x 5 columns]
```

### 主营构成-东财

接口: stock_zygc_em

目标地址: https://emweb.securities.eastmoney.com/PC_HSF10/BusinessAnalysis/Index?type=web&code=SH688041#

描述: 东方财富网-个股-主营构成

限量: 单次返回所有历史数据

输入参数

| 名称     | 类型  | 描述                |
|--------|-----|-------------------|
| symbol | str | symbol="SH688041" |

输出参数

| 名称   | 类型      | 描述      |
|------|---------|---------|
| 股票代码 | object  | -       |
| 报告日期 | object  | -       |
| 分类类型 | object  | -       |
| 主营构成 | int64   | -       |
| 主营收入 | float64 | 注意单位: 元 |
| 收入比例 | float64 | -       |
| 主营成本 | float64 | 注意单位: 元 |
| 成本比例 | float64 | -       |
| 主营利润 | float64 | 注意单位: 元 |
| 利润比例 | float64 | -       |
| 毛利率  | float64 | -       |

接口示例

```python
import akshare as ak

stock_zygc_em_df = ak.stock_zygc_em(symbol="SH688041")
print(stock_zygc_em_df)
```

数据示例

```
    股票代码  报告日期   分类类型  ...      主营利润      利润比例       毛利率
0   688041  2024-06-30  按产品分类  ...  2.385020e+09  0.999313  0.634303
1   688041  2024-06-30  按产品分类  ...  1.639645e+06  0.000687  0.575505
2   688041  2024-06-30  按地区分类  ...  2.386659e+09  1.000000  0.634259
3   688041  2023-12-31    NaN  ...  3.587141e+09  0.999963  0.596682
4   688041  2023-12-31    NaN  ...  1.337029e+05  0.000037  0.708626
..     ...         ...    ...  ...           ...       ...       ...
60  688041  2018-12-31  按产品分类  ...  3.538980e+07  0.874818  0.841592
61  688041  2018-12-31  按产品分类  ...  4.352600e+06  0.107594  0.792982
62  688041  2018-12-31  按产品分类  ...           NaN       NaN       NaN
63  688041  2018-12-31  按地区分类  ...           NaN       NaN       NaN
64  688041  2018-12-31  按地区分类  ...           NaN       NaN       NaN
[65 rows x 11 columns]
```

### 财经内容精选

接口: stock_news_main_cx

目标地址: https://cxdata.caixin.com/pc/

描述: 财新网-财新数据通-最新

限量: 返回最新 100 条新闻数据

输入参数

| 名称 | 类型 | 描述 |
|----|----|----|
| -  | -  | -  |

输出参数

| 名称            | 类型     | 描述 |
|---------------|--------|----|
| tag           | object | -  |
| summary       | object | -  |
| url           | object | -  |

接口示例

```python
import akshare as ak

stock_news_main_cx_df = ak.stock_news_main_cx()
print(stock_news_main_cx_df)
```

数据示例

```
      tag  ...                                                url
0    今日热点  ...  https://database.caixin.com/2025-12-25/1023970...
5    市场动态  ...  https://database.caixin.com/2025-12-25/1023969...
6    市场动态  ...  https://database.caixin.com/2025-12-25/1023969...
9    市场动态  ...  https://database.caixin.com/2025-12-25/1023969...
10   市场动态  ...  https://database.caixin.com/2025-12-25/1023969...
..    ...  ...                                                ...
105  市场动态  ...  https://database.caixin.com/2025-12-15/1023934...
106  市场动态  ...  https://database.caixin.com/2025-12-15/1023934...
107  市场动态  ...  https://database.caixin.com/2025-12-15/1023934...
108  市场洞察  ...  https://database.caixin.com/2025-12-15/1023933...
109  市场洞察  ...  https://database.caixin.com/2025-12-15/1023933...
[100 rows x 3 columns]
```

### 基本面数据

#### 大盘拥挤度

接口: stock_a_congestion_lg

目标地址: https://legulegu.com/stockdata/ashares-congestion

描述: 乐咕乐股-大盘拥挤度

限量: 单次获取近 4 年的历史数据

输入参数

| 名称  | 类型  | 描述  |
|-----|-----|-----|
| -   | -   | -   |

输出参数

| 名称         | 类型      | 描述  |
|------------|---------|-----|
| date       | object  | 日期  |
| close      | float64 | 收盘价 |
| congestion | float64 | 拥挤度 |

接口示例

```python
import akshare as ak

stock_a_congestion_lg_df = ak.stock_a_congestion_lg()
print(stock_a_congestion_lg_df)
```

数据示例

```
           date    close  congestion
0    2020-04-27  2815.49      0.3783
1    2020-04-28  2810.02      0.3797
2    2020-04-29  2822.44      0.3876
3    2020-04-30  2860.08      0.4009
4    2020-05-06  2878.14      0.4080
..          ...      ...         ...
962  2024-04-18  3074.22      0.3848
963  2024-04-19  3065.26      0.3896
964  2024-04-22  3044.60      0.3834
965  2024-04-23  3021.98      0.3808
966  2024-04-24  3044.82      0.3786
[967 rows x 3 columns]
```

#### 股债利差

接口: stock_ebs_lg

目标地址: https://legulegu.com/stockdata/equity-bond-spread

描述: 乐咕乐股-股债利差

限量: 单次所有历史数据

输入参数

| 名称  | 类型  | 描述  |
|-----|-----|-----|
| -   | -   | -   |

输出参数

| 名称      | 类型      | 描述  |
|---------|---------|-----|
| 日期      | object  | -   |
| 沪深300指数 | float64 | -   |
| 股债利差    | float64 | -   |
| 股债利差均线  | float64 | -   |

接口示例

```python
import akshare as ak

stock_ebs_lg_df = ak.stock_ebs_lg()
print(stock_ebs_lg_df)
```

数据示例

```
            日期  沪深300指数   股债利差 股债利差均线
0     2005-04-08  1003.45  0.022656  0.022656
1     2005-04-11   995.42  0.021938  0.022297
2     2005-04-12   978.70  0.024697  0.023097
3     2005-04-13  1000.90  0.022538  0.022957
4     2005-04-14   986.98  0.022811  0.022928
          ...      ...       ...       ...
4619  2024-04-18  3569.80  0.064876  0.061882
4620  2024-04-19  3541.66  0.064949  0.061909
4621  2024-04-22  3530.90  0.065748  0.061983
4622  2024-04-23  3506.22  0.066550  0.062014
4623  2024-04-24  3521.62  0.065847  0.062020
[4624 rows x 4 columns]
```

#### 巴菲特指标

接口: stock_buffett_index_lg

目标地址: https://legulegu.com/stockdata/marketcap-gdp

描述: 乐估乐股-底部研究-巴菲特指标

限量: 单次获取所有历史数据

输入参数

| 名称  | 类型  | 描述  |
|-----|-----|-----|
| -   | -   | -   |

输出参数

| 名称     | 类型      | 描述                             |
|--------|---------|--------------------------------|
| 日期     | object  | 交易日                            |
| 收盘价    | float64 | -                              |
| 总市值    | float64 | A股收盘价*已发行股票总股本（A股+B股+H股）       |
| GDP    | float64 | 上年度国内生产总值（例如：2019年，则取2018年GDP） |
| 近十年分位数 | float64 | 当前"总市值/GDP"在历史数据上的分位数          |
| 总历史分位数 | float64 | 当前"总市值/GDP"在历史数据上的分位数          |

接口示例

```python
import akshare as ak

stock_buffett_index_lg_df = ak.stock_buffett_index_lg()
print(stock_buffett_index_lg_df)
```

数据示例

```
            日期   收盘价       总市值      GDP   近十年分位数  总历史分位数
0     2005-04-07  1003.45   38470.47   161840.16  1.00000  1.00000
1     2005-04-10   995.42   39184.81   161840.16  1.00000  1.00000
2     2005-04-11   978.70   38955.09   161840.16  0.66667  0.66667
3     2005-04-12  1000.90   38287.33   161840.16  0.25000  0.25000
4     2005-04-13   986.98   39166.32   161840.16  0.80000  0.80000
...          ...      ...        ...         ...      ...      ...
4646  2024-05-26  3635.71  894146.43  1260582.10  0.34239  0.47837
4647  2024-05-27  3609.17  888429.78  1260582.10  0.32593  0.46601
4648  2024-05-28  3613.52  889703.17  1260582.10  0.32840  0.46870
4649  2024-05-29  3594.31  884208.63  1260582.10  0.31235  0.45699
4650  2024-05-30  3579.92  884322.56  1260582.10  0.31304  0.45732
[4651 rows x 6 columns]
```


#### 主板市盈率

接口: stock_market_pe_lg

目标地址: https://legulegu.com/stockdata/shanghaiPE

描述: 乐咕乐股-主板市盈率

限量: 单次获取指定 symbol 的所有数据

输入参数

| 名称     | 类型  | 描述                                                |
|--------|-----|---------------------------------------------------|
| symbol | str | symbol="上证"; choice of {"上证", "深证", "创业板", "科创版"} |

输出参数-上证, 深证, 创业板

| 名称    | 类型      | 描述  |
|-------|---------|-----|
| 日期    | object  | -   |
| 指数    | float64 | -   |
| 平均市盈率 | float64 | -   |

接口示例-上证, 深证, 创业板

```python
import akshare as ak

stock_market_pe_lg_df = ak.stock_market_pe_lg(symbol="上证")
print(stock_market_pe_lg_df)
```

数据示例-上证, 深证, 创业板

```
        日期       指数  平均市盈率
0    1999-01-29  1134.67  34.03
1    1999-02-09  1090.08  33.50
2    1999-03-31  1158.05  34.30
3    1999-04-30  1120.92  34.39
4    1999-05-31  1279.32  35.30
..          ...      ...    ...
306  2024-06-28  2967.40  12.69
307  2024-07-31  2938.75  12.55
308  2024-08-30  2842.21  12.16
309  2024-09-30  3336.50  14.24
310  2024-10-18  3261.56  13.89
[311 rows x 3 columns]
```

输出参数-科创版

| 名称  | 类型      | 描述  |
|-----|---------|-----|
| 日期  | object  | -   |
| 总市值 | float64 | -   |
| 市盈率 | float64 | -   |

接口示例-科创版

```python
import akshare as ak

stock_market_pe_lg_df = ak.stock_market_pe_lg(symbol="科创版")
print(stock_market_pe_lg_df)
```

数据示例-科创版

```
        日期       总市值    市盈率
0     2019-07-22   5293.39  81.43
1     2019-07-23   4821.95  74.18
2     2019-07-24   5135.78  79.00
3     2019-07-25   5373.12  82.65
4     2019-07-26   5000.56  76.92
...          ...       ...    ...
1265  2024-10-14  58559.78  39.19
1266  2024-10-15  56996.68  38.18
1267  2024-10-16  55961.92  37.50
1268  2024-10-17  56181.48  37.54
1269  2024-10-18  61039.80  40.72
[1270 rows x 3 columns]
```

#### 指数市盈率

接口: stock_index_pe_lg

目标地址: https://legulegu.com/stockdata/sz50-ttm-lyr

描述: 乐咕乐股-指数市盈率

限量: 单次获取指定 symbol 的所有数据

输入参数

| 名称     | 类型  | 描述                                                                                                                                  |
|--------|-----|-------------------------------------------------------------------------------------------------------------------------------------|
| symbol | str | symbol="上证50"; choice of {"上证50", "沪深300", "上证380", "创业板50", "中证500", "上证180", "深证红利", "深证100", "中证1000", "上证红利", "中证100", "中证800"} |

输出参数

| 名称       | 类型      | 描述  |
|----------|---------|-----|
| 日期       | object  | -   |
| 指数       | float64 | -   |
| 等权静态市盈率  | float64 | -   |
| 静态市盈率    | float64 | -   |
| 静态市盈率中位数 | float64 | -   |
| 等权滚动市盈率  | float64 | -   |
| 滚动市盈率    | float64 | -   |
| 滚动市盈率中位数 | float64 | -   |

接口示例

```python
import akshare as ak

stock_index_pe_lg_df = ak.stock_index_pe_lg(symbol="上证50")
print(stock_index_pe_lg_df)
```

数据示例

```
      日期         指数  等权静态市盈率  静态市盈率  静态市盈率中位数  等权滚动市盈率  滚动市盈率  滚动市盈率中位数
0     2005-01-05   831.43    32.48  20.69     27.02    29.52  14.93     18.97
1     2005-01-06   822.50    32.57  20.37     27.00    29.74  14.69     18.81
2     2005-01-07   823.62    32.59  20.50     27.10    29.81  14.79     18.73
3     2005-01-10   832.99    32.99  20.58     27.29    30.13  14.83     19.07
4     2005-01-11   837.86    33.13  20.69     27.25    30.26  14.91     19.26
...          ...      ...      ...    ...       ...      ...    ...       ...
4800  2024-10-14  2723.18    33.03  11.48     17.17    32.32  11.27     17.79
4801  2024-10-15  2655.12    32.16  11.17     16.68    31.50  10.97     17.43
4802  2024-10-16  2650.18    31.65  11.19     16.42    30.20  11.00     17.45
4803  2024-10-17  2610.47    31.47  11.05     16.13    30.05  10.86     16.94
4804  2024-10-18  2681.91    33.61  11.29     16.60    32.22  11.09     17.35
[4805 rows x 8 columns]
```

### 股票热度

#### 股票热度-雪球

##### 关注排行榜

接口: stock_hot_follow_xq

目标地址: https://xueqiu.com/hq

描述: 雪球-沪深股市-热度排行榜-关注排行榜

限量: 单次返回指定 symbol 的排行数据

输入参数

| 名称     | 类型  | 描述                                      |
|--------|-----|-----------------------------------------|
| symbol | str | symbol="最热门"; choice of {"本周新增", "最热门"} |

输出参数

| 名称   | 类型      | 描述      |
|------|---------|---------|
| 股票代码 | object  | -       |
| 股票简称 | object  | -       |
| 关注   | float64 | -       |
| 最新价  | float64 | 注意单位: 元 |

接口示例

```python
import akshare as ak

stock_hot_follow_xq_df = ak.stock_hot_follow_xq(symbol="最热门")
print(stock_hot_follow_xq_df)
```

数据示例

```
     股票代码  股票简称         关注      最新价
0     SH600519  贵州茅台  2763065.0  1663.36
1     SH601318  中国平安  2321952.0    38.97
2     SH600036  招商银行  2039407.0    28.29
3     SZ000651  格力电器  1768422.0    32.98
4     SZ002594   比亚迪  1494585.0   192.68
        ...   ...        ...      ...
5420  BJ836957  汉维科技      180.0     9.42
5421  BJ836942  恒立钻具      178.0    13.07
5422  BJ836419  万德股份      176.0    11.15
5423  BJ873690   N捷众       30.0    21.01
5424  SZ300307  慈星股份        NaN     6.20
[5425 rows x 4 columns]
```

##### 讨论排行榜

接口: stock_hot_tweet_xq

目标地址: https://xueqiu.com/hq

描述: 雪球-沪深股市-热度排行榜-讨论排行榜

限量: 单次返回指定 symbol 的排行数据

输入参数

| 名称     | 类型  | 描述                                      |
|--------|-----|-----------------------------------------|
| symbol | str | symbol="最热门"; choice of {"本周新增", "最热门"} |

输出参数

| 名称   | 类型      | 描述      |
|------|---------|---------|
| 股票代码 | object  | -       |
| 股票简称 | object  | -       |
| 关注   | float64 | -       |
| 最新价  | float64 | 注意单位: 元 |

接口示例

```python
import akshare as ak

stock_hot_tweet_xq_df = ak.stock_hot_tweet_xq(symbol="最热门")
print(stock_hot_tweet_xq_df)
```

数据示例

```
      股票代码  股票简称     关注       最新价
0     SZ002594   比亚迪  89745   192.680
1     SH600519  贵州茅台  85990  1663.360
2     SZ300750  宁德时代  52705   150.900
3     SZ000977  浪潮信息  50664    30.160
4     SZ002229  鸿博股份  46794    24.690
        ...   ...    ...       ...
5420  SH900913  国新B股      0     0.246
5421  SH900901  云赛B股      0     0.496
5422  BJ870508  丰安股份      0    12.530
5423  BJ836149  旭杰科技      0     7.970
5424  BJ831175  派诺科技      0    22.490
[5425 rows x 4 columns]
```

##### 交易排行榜

接口: stock_hot_deal_xq

目标地址: https://xueqiu.com/hq

描述: 雪球-沪深股市-热度排行榜-交易排行榜

限量: 单次返回指定 symbol 的排行数据

输入参数

| 名称     | 类型  | 描述                                      |
|--------|-----|-----------------------------------------|
| symbol | str | symbol="最热门"; choice of {"本周新增", "最热门"} |

输出参数

| 名称   | 类型      | 描述      |
|------|---------|---------|
| 股票代码 | object  | -       |
| 股票简称 | object  | -       |
| 关注   | float64 | -       |
| 最新价  | float64 | 注意单位: 元 |

接口示例

```python
import akshare as ak

stock_hot_deal_xq_df = ak.stock_hot_deal_xq(symbol="最热门")
print(stock_hot_deal_xq_df)
```

数据示例

```
     股票代码  股票简称   关注      最新价
0     SH601318  中国平安  304    38.97
1     SZ002229  鸿博股份  258    24.69
2     SH600519  贵州茅台  257  1663.36
3     SZ002594   比亚迪  257   192.68
4     SH600880  博瑞传播  231     4.90
        ...   ...  ...      ...
5420  SZ300932  三友联众    0    15.95
5421  SZ300956  英力股份    0    18.21
5422  SH688618  三旺通信    0    52.82
5423  BJ836149  旭杰科技    0     7.97
5424  SH688655   迅捷兴    0    14.64
[5425 rows x 4 columns]
```

#### 股票热度-东财

##### 人气榜-A股

接口: stock_hot_rank_em

目标地址: http://guba.eastmoney.com/rank/

描述: 东方财富网站-股票热度

限量: 单次返回当前交易日前 100 个股票的人气排名数据

输入参数

| 名称  | 类型  | 描述  |
|-----|-----|-----|
| -   | -   | -   |

输出参数

| 名称   | 类型      | 描述      |
|------|---------|---------|
| 当前排名 | int64   | -       |
| 代码   | object  | -       |
| 股票名称 | object  | -       |
| 最新价  | float64 | -       |
| 涨跌额  | float64 | -       |
| 涨跌幅  | float64 | 注意单位: % |

接口示例

```python
import akshare as ak

stock_hot_rank_em_df = ak.stock_hot_rank_em()
print(stock_hot_rank_em_df)
```

数据示例

```
    当前排名   代码  股票名称    最新价       涨跌额    涨跌幅
0      1  SZ002261  拓维信息  18.83  0.090384   0.48
1      2  SH603000   人民网  34.35  2.881965   8.39
2      3  SH601127   赛力斯  33.72  3.378744  10.02
3      4  SZ002229  鸿博股份  35.09  0.021054   0.06
4      5  SZ000936  华西股份  10.41  1.045164  10.04
..   ...       ...   ...    ...       ...    ...
95    96  SZ002585  双星新材   9.69  0.968031   9.99
96    97  SZ002670  国盛金控   8.46  0.520290   6.15
97    98  SZ300116   保力新   1.53  0.191250  12.50
98    99  SH603533  掌阅科技  33.14 -3.231150  -9.75
99   100  SZ301368  丰立智能  58.32  3.563352   6.11
[100 rows x 6 columns]
```

#### 热门关键词

接口: stock_hot_keyword_em

目标地址: http://guba.eastmoney.com/rank/stock?code=000665

描述: 东方财富-个股人气榜-热门关键词

限量: 单次返回指定 symbol 的最近交易日时点数据

输入参数

| 名称     | 类型  | 描述                |
|--------|-----|-------------------|
| symbol | str | symbol="SZ000665" |

输出参数

| 名称   | 类型     | 描述  |
|------|--------|-----|
| 时间   | object | -   |
| 股票代码 | object | -   |
| 概念名称 | object | -   |
| 概念代码 | object | -   |
| 热度   | int64  | -   |

接口示例

```python
import akshare as ak

stock_hot_keyword_em_df = ak.stock_hot_keyword_em(symbol="SZ000665")
print(stock_hot_keyword_em_df)
```

数据示例

```
               时间      股票代码   概念名称    概念代码  热度
0  2022-02-28 12:00:00  SZ000665  元宇宙概念  BK1009  2138
1  2022-02-28 12:00:00  SZ000665     广电  BK0904  1082
2  2022-02-28 12:00:00  SZ000665    云计算  BK0579   411
3  2022-02-28 12:00:00  SZ000665   虚拟现实  BK0722   152
4  2022-02-28 12:00:00  SZ000665   彩票概念  BK0671   131
5  2022-02-28 12:00:00  SZ000665   转债标的  BK0528    51
6  2022-02-28 12:00:00  SZ000665   华为概念  BK0854    36
7  2022-02-28 12:00:00  SZ000665   智慧城市  BK0628    31
8  2022-02-28 12:00:00  SZ000665   预盈预增  BK0571    13
9  2022-02-28 12:00:00  SZ000665   超清视频  BK0859     1
```

### 资讯数据


#### 电报-财联社

接口：stock_info_global_cls

目标地址：https://www.cls.cn/telegraph

描述：财联社-电报

限量：单次返回指定 symbol 的最近 20 条财联社-电报的数据

输入参数

| 名称     | 类型  | 描述                                 |
|--------|-----|------------------------------------|
| symbol | str | symbol="全部"；choice of {"全部", "重点"} |

输出参数

| 名称   | 类型     | 描述  |
|------|--------|-----|
| 标题   | object | -   |
| 内容   | object | -   |
| 发布日期 | object | -   |
| 发布时间 | object | -   |

接口示例：

```python
import akshare as ak

stock_info_global_cls_df = ak.stock_info_global_cls(symbol="全部")
print(stock_info_global_cls_df)
```

数据示例

```
                               标题  ...      发布时间
0    华为轮值董事长徐直军谈鸿蒙生态未来目标：拥有10万个应用  ...  14:05:03
1       中国牵头首个冷链物流无接触配送领域国际标准正式发布  ...  14:12:02
2           以军袭击黎巴嫩首都住宅楼 死亡人数升至5人  ...  14:37:34
3            上交所与三大石油石化集团将进一步深化合作  ...  14:50:34
4                                  ...  14:56:22
5    至少19人食用后患病 美国企业紧急召回近76吨牛肉泥产品  ...  15:13:18
6       《加强长江流域生物多样性司法保护倡议书》在武汉发布  ...  15:27:53
7               阿联酋哈伊马角酋长一行到访亿航智能  ...  15:41:35
8           以军称空袭贝鲁特南郊多个真主党武装军事目标  ...  15:43:30
9          以军空袭加沙地带多地 致17名巴勒斯坦人死亡  ...  15:46:34
10             北约秘书长在美国佛州与特朗普举行会谈  ...  15:49:04
11     经济观察报：央国企市值管理更多相关政策在酝酿和推进中  ...  15:56:06
12      华为徐直军：鸿蒙生态就是基于开源鸿蒙共建共享的生态  ...  16:00:29
13  我国牵头的首个工业化建造自动标识与数据采集应用国际标准发布  ...  16:02:03
14     AI辅助诊断首次被列入 国家医保局解读17批价格立项  ...  16:12:22
15            以军袭击贝鲁特中部住宅楼 已致9人死亡  ...  16:32:07
16        俄宣布12月1日起临时禁止废旧贵金属出口6个月  ...  16:36:40
17                                 ...  16:41:55
18          波兰农民在波乌边境抗议 将封锁梅迪卡过境点  ...  16:56:41
19            吉林省将迎大范围明显雨雪及寒潮大风天气  ...  17:17:38
[20 rows x 4 columns]
```


## [AKShare](https://github.com/akfamily/akshare) 公募基金数据

### 基金排行

#### 场内交易基金排行榜

接口: fund_exchange_rank_em

目标地址: https://fund.eastmoney.com/data/fbsfundranking.html

描述: 东方财富网-数据中心-场内交易基金排行榜

限量: 单次返回当前时刻所有数据, 每个交易日 17 点后更新

输入参数

| 名称  | 类型  | 描述  |
|-----|-----|-----|
| -   | -   | -   |

输出参数

| 名称   | 类型      | 描述      |
|------|---------|---------|
| 序号   | int64   | -       |
| 基金代码 | object  | -       |
| 基金简称 | object  | -       |
| 类型   | object  | -       |
| 日期   | object  | -       |
| 单位净值 | float64 | -       |
| 累计净值 | float64 | -       |
| 近1周  | float64 | 注意单位: % |
| 近1月  | float64 | 注意单位: % |
| 近3月  | float64 | 注意单位: % |
| 近6月  | float64 | 注意单位: % |
| 近1年  | float64 | 注意单位: % |
| 近2年  | float64 | 注意单位: % |
| 近3年  | float64 | 注意单位: % |
| 今年来  | float64 | 注意单位: % |
| 成立来  | float64 | 注意单位: % |
| 成立日期 | object  | -       |

接口示例

```python
import akshare as ak

fund_exchange_rank_em_df = ak.fund_exchange_rank_em()
print(fund_exchange_rank_em_df)
```

数据示例

```
      序号    基金代码                基金简称  ...    今年来     成立来        成立日期
0      1  513300  华夏纳斯达克100ETF(QDII)  ...   8.31   62.36  2020-10-22
1      2  159632  华安纳斯达克100ETF(QDII)  ...   6.52   46.67  2022-07-21
2      3  513100        国泰纳斯达克100ETF  ...   7.14  545.00  2013-04-25
3      4  159941        广发纳斯达克100ETF  ...   7.07  288.28  2015-06-10
4      5  513520        华夏野村日经225ETF  ...  11.69   42.39  2019-06-12
..   ...     ...                 ...  ...    ...     ...         ...
875  876  159573       华夏创业板中盘200ETF  ... -15.70  -15.30  2023-12-15
876  877  159577      汇添富MSCI美国50ETF  ...    NaN    0.13  2024-02-05
877  878  159549     天弘中证红利低波动100ETF  ...   3.48    2.38  2023-11-23
878  879  159562    华夏中证沪深港黄金产业股票ETF  ...    NaN    3.62  2024-01-11
879  880  560300        汇添富中证电信主题ETF  ...   4.35    2.64  2023-12-05
[880 rows x 17 columns]
```
### 基金业绩-雪球

接口: fund_individual_achievement_xq

目标地址: https://danjuanfunds.com/rn/funding/:code/RankInfo?symbol=000001&fd_type=2&btn_pos=1

描述: 雪球基金-基金详情-基金业绩-详情

限量: 单次返回单只基金业绩详情

输入参数

| 名称      | 类型    | 描述                      |
|---------|-------|-------------------------|
| symbol  | str   | symbol="000001"; 基金代码   |
| timeout | float | timeout=None; 默认不设置超时参数 |

输出参数

| 名称       | 类型      | 描述      |
|----------|---------|---------|
| 业绩类型     | object  | -       |
| 周期       | object  | -       |
| 本产品区间收益  | float64 | 注意单位: % |
| 本产品最大回撒  | float64 | 注意单位: % |
| 周期收益同类排名 | object  | -       |

接口示例

```python
import akshare as ak

fund_individual_achievement_xq_df = ak.fund_individual_achievement_xq(symbol="000001")
print(fund_individual_achievement_xq_df)
```

数据示例

```
    业绩类型  周期    本产品区间收益 本产品最大回撒 周期收益同类排名
0   年度业绩  成立以来  399.458300    54.55   128/7671
1   年度业绩  今年以来   -0.768251    26.58  4175/7674
2   年度业绩  2023  -21.990000    26.58  1631/1843
3   年度业绩  2022  -17.040000    27.87   872/1740
4   年度业绩  2021   -7.400000    21.63  1505/1625
5   年度业绩  2020   27.660000    14.39  1023/1549
6   年度业绩  2019   25.970000    11.81   854/1471
7   年度业绩  2018  -19.050000    23.65   761/1278
8   年度业绩  2017   17.110000     6.94   224/1068
9   年度业绩  2016  -22.720000    24.67    609/681
10  年度业绩  2015   25.860000    40.81    192/298
11  年度业绩  2014   15.270000    10.66    134/204
12  年度业绩  2013   15.710000     9.96     53/156
13  年度业绩  2012    7.250000    12.67     39/132
14  年度业绩  2011  -24.450000    29.07     81/114
15  年度业绩  2010    3.560000    16.23     61/103
16  年度业绩  2009   67.370000    21.29      38/87
17  年度业绩  2008  -44.020000    53.97      18/73
18  年度业绩  2007  130.730000    15.58      13/60
19  年度业绩  2006  118.050000    12.46      20/45
20  年度业绩  2005   -5.330000    18.35      32/33
21  年度业绩  2004    3.910000    18.06       5/16
22  年度业绩  2003   13.090000    12.68        7/7
23  年度业绩  2002   -3.090000    11.93        1/1
24  阶段业绩   近1月   -4.791167      NaN  6390/7643
25  阶段业绩   近3月  -11.731204    13.78  7244/7564
26  阶段业绩   近6月  -17.377404    19.72  5985/7313
27  阶段业绩   近1年  -22.592303    26.58  5891/6832
28  阶段业绩   近3年  -40.505159    48.55  3301/3783
29  阶段业绩   近5年   -3.250474    48.55  2300/2414
```

### 基金数据分析

接口: fund_individual_analysis_xq

目标地址: https://danjuanfunds.com/funding/000001

描述: 雪球基金-基金详情-数据分析

限量: 返回单只基金历史表现分析数据

输入参数

| 名称      | 类型    | 描述                      |
|---------|-------|-------------------------|
| symbol  | str   | symbol="000001"; 基金代码   |
| timeout | float | timeout=None; 默认不设置超时参数 |

输出参数

| 名称       | 类型      | 描述     |
|----------|---------|--------|
| 周期       | object  | -      |
| 较同类风险收益比 | int64   | 注意单位：% |
| 较同类抗风险波动 | int64   | 注意单位：% |
| 年化波动率    | float64 | 注意单位：% |
| 年化夏普比率   | float64 | -      |
| 最大回撤     | float64 | 注意单位：% |

接口示例

```python
import akshare as ak

fund_individual_analysis_xq_df = ak.fund_individual_analysis_xq(symbol="000001")
print(fund_individual_analysis_xq_df)
```

数据示例

```
   周期  较同类风险收益比 较同类抗风险波动  年化波动率  年化夏普比率   最大回撤
0  近1年         3        61  12.72   -1.89  26.58
1  近3年         9        56  18.66   -0.93  48.55
2  近5年         2        57  19.04   -0.11  48.55
```

### 基金盈利概率

接口: fund_individual_profit_probability_xq

目标地址: https://danjuanfunds.com/funding/000001

描述: 雪球基金-基金详情-盈利概率；历史任意时点买入，持有满X时间，盈利概率，以及平均收益

限量: 单次返回单只基金历史任意时点买入，持有满 X 时间，盈利概率，以及平均收益

输入参数

| 名称      | 类型    | 描述                      |
|---------|-------|-------------------------|
| symbol  | str   | symbol="000001"; 基金代码   |
| timeout | float | timeout=None; 默认不设置超时参数 |

输出参数

| 名称   | 类型     | 描述     |
|------|--------|--------|
| 持有时长 | object | -      |
| 盈利概率 | object | 注意单位：% |
| 平均收益 | object | 注意单位：% |

接口示例

```python
import akshare as ak

fund_individual_profit_probability_xq_df = ak.fund_individual_profit_probability_xq(symbol="000001")
print(fund_individual_profit_probability_xq_df)
```

数据示例

```
  持有时长  盈利概率 平均收益
0  满6个月    53   5.97
1   满1年    59  14.23
2   满2年    66  32.34
3   满3年    76  51.16
```

### 基金持仓资产比例

接口: fund_individual_detail_hold_xq

目标地址: https://danjuanfunds.com/rn/fund-detail/archive?id=103&code=000001

描述: 雪球基金-基金详情-基金持仓-详情

限量: 单次返回单只基金指定日期的持仓大类资产比例

输入参数

| 名称      | 类型    | 描述                      |
|---------|-------|-------------------------|
| symbol  | str   | symbol="000001"; 基金代码   |
| date    | str   | date="20231231"; 季度日期   |
| timeout | float | timeout=None; 默认不设置超时参数 |

输出参数

| 名称   | 类型      | 描述     |
|------|---------|--------|
| 资产类型 | object  | -      |
| 仓位占比 | float64 | 注意单位：% |

接口示例

```python
import akshare as ak

fund_individual_detail_hold_xq_df = ak.fund_individual_detail_hold_xq(symbol="002804", date="20231231")
print(fund_individual_detail_hold_xq_df)
```

数据示例

```
  资产类型   仓位占比
0   股票  51.95
1   现金  19.51
2   其他  29.09
```

### 基金基本概况

接口: fund_overview_em

目标地址: https://fundf10.eastmoney.com/jbgk_015641.html

描述: 天天基金-基金档案-基本概况

限量: 单次返回指定 symbol 的数据

输入参数

| 名称     | 类型  | 描述                    |
|--------|-----|-----------------------|
| symbol | str | symbol="015641"; 基金代码 |

输出参数

| 名称      | 类型     | 描述 |
|---------|--------|----|
| 基金全称    | object | -  |
| 基金简称    | object | -  |
| 基金代码    | object | -  |
| 基金类型    | object | -  |
| 发行日期    | object | -  |
| 成立日期/规模 | object | -  |
| 资产规模    | object | -  |
| 份额规模    | object | -  |
| 基金管理人   | object | -  |
| 基金托管人   | object | -  |
| 基金经理人   | object | -  |
| 成立来分红   | object | -  |
| 管理费率    | object | -  |
| 托管费率    | object | -  |
| 销售服务费率  | object | -  |
| 最高认购费率  | object | -  |
| 业绩比较基准  | object | -  |
| 跟踪标的    | object | -  |

接口示例

```python
import akshare as ak

fund_overview_em_df = ak.fund_overview_em(symbol="015641")
print(fund_overview_em_df)
```

数据示例

```
                 基金全称          基金简称        基金代码 基金类型         发行日期                成立日期/规模  ...       跟踪标的
0  银华数字经济股票型发起式证券投资基金  银华数字经济股票发起式A  015641（前端）  股票型  2022年05月12日  2022年05月20日 / 0.137亿份  ...  该基金无跟踪标的
[1 rows x 18 columns]
```
### 基金持仓

接口: fund_portfolio_hold_em

目标地址: https://fundf10.eastmoney.com/ccmx_000001.html

描述: 天天基金网-基金档案-投资组合-基金持仓

限量: 单次返回指定 symbol 和 date 的所有持仓数据

输入参数

| 名称     | 类型  | 描述                                                       |
|--------|-----|----------------------------------------------------------|
| symbol | str | symbol="000001"; 基金代码, 可以通过调用 **ak.fund_name_em()** 接口获取 |
| date   | str | date="2024"; 指定年份                                        |

输出参数

| 名称    | 类型      | 描述       |
|-------|---------|----------|
| 序号    | int64   | -        |
| 股票代码  | object  | -        |
| 股票名称  | object  | -        |
| 占净值比例 | float64 | 注意单位: %  |
| 持股数   | float64 | 注意单位: 万股 |
| 持仓市值  | float64 | 注意单位: 万元 |
| 季度    | object  | -        |

接口示例

```python
import akshare as ak

fund_portfolio_hold_em_df = ak.fund_portfolio_hold_em(symbol="000001", date="2024")
print(fund_portfolio_hold_em_df)
```

数据示例

```
   序号 股票代码  股票名称  占净值比例 持股数 持仓市值              季度
0   1  002025   航天电器   3.46  209.92  7947.67  2024年1季度股票投资明细
1   2  600862   中航高科   3.24  380.43  7441.16  2024年1季度股票投资明细
2   3  600941   中国移动   2.86   62.11  6568.75  2024年1季度股票投资明细
3   4  300395    菲利华   2.80  216.80  6417.42  2024年1季度股票投资明细
4   5  300034   钢研高纳   2.69  403.16  6168.33  2024年1季度股票投资明细
5   6  002371   北方华创   2.67   20.07  6134.03  2024年1季度股票投资明细
6   7  002475   立讯精密   2.30  179.77  5287.04  2024年1季度股票投资明细
7   8  600276   恒瑞医药   2.22  111.06  5105.35  2024年1季度股票投资明细
8   9  600522   中天科技   1.99  325.78  4570.69  2024年1季度股票投资明细
9  10  000100  TCL科技   1.82  893.37  4172.03  2024年1季度股票投资明细
```


### 行业配置

接口: fund_portfolio_industry_allocation_em

目标地址: https://fundf10.eastmoney.com/hytz_000001.html

描述: 天天基金网-基金档案-投资组合-行业配置

限量: 单次返回指定 symbol 和 date 的所有持仓数据

输入参数

| 名称     | 类型  | 描述                                                       |
|--------|-----|----------------------------------------------------------|
| symbol | str | symbol="000001"; 基金代码, 可以通过调用 **ak.fund_name_em()** 接口获取 |
| date   | str | date="2023"; 指定年份                                        |

输出参数

| 名称    | 类型      | 描述       |
|-------|---------|----------|
| 序号    | int64   | -        |
| 行业类别  | object  | -        |
| 占净值比例 | float64 | 注意单位: %  |
| 市值    | float64 | 注意单位: 万元 |
| 截止时间  | object  | -        |

接口示例

```python
import akshare as ak

fund_portfolio_industry_allocation_em_df = ak.fund_portfolio_industry_allocation_em(symbol="000001", date="2023")
print(fund_portfolio_industry_allocation_em_df)
```

数据示例

```
    序号              行业类别  占净值比例             市值        截止时间
0    1               制造业  69.53  189787.963063  2023-09-30
1    2        科学研究和技术服务业   1.61    4388.935702  2023-09-30
2    3            批发和零售业   1.43    3896.705281  2023-09-30
3    4               金融业   1.17    3195.408100  2023-09-30
4    5               采矿业   1.17    3194.758900  2023-09-30
5    6              房地产业   0.96    2629.990410  2023-09-30
6    7          租赁和商务服务业   0.62    1688.184585  2023-09-30
7    8   信息传输、软件和信息技术服务业   0.52    1423.173173  2023-09-30
8    9               建筑业   0.21     571.626784  2023-09-30
9   10           卫生和社会工作   0.20     538.414546  2023-09-30
10  11     水利、环境和公共设施管理业   0.00       4.560998  2023-09-30
11  12  电力、热力、燃气及水生产和供应业   0.00       3.356397  2023-09-30
12  13               制造业  68.81  201157.775395  2023-06-30
13  14            批发和零售业   1.41    4129.958752  2023-06-30
14  15              房地产业   1.39    4067.173378  2023-06-30
15  16        科学研究和技术服务业   1.26    3684.969783  2023-06-30
16  17               采矿业   0.93    2716.791300  2023-06-30
17  18   信息传输、软件和信息技术服务业   0.78    2268.536719  2023-06-30
18  19               金融业   0.67    1962.987600  2023-06-30
19  20          租赁和商务服务业   0.35    1021.826600  2023-06-30
20  21               建筑业   0.34     982.386764  2023-06-30
21  22           卫生和社会工作   0.33     972.647166  2023-06-30
22  23  电力、热力、燃气及水生产和供应业   0.18     525.067947  2023-06-30
23  24     水利、环境和公共设施管理业   0.00       2.256657  2023-06-30
24  25               制造业  65.89  193354.962582  2023-03-31
25  26        科学研究和技术服务业   3.92   11490.739335  2023-03-31
26  27          租赁和商务服务业   1.90    5584.193500  2023-03-31
27  28   信息传输、软件和信息技术服务业   1.45    4256.190176  2023-03-31
28  29               金融业   1.35    3952.021810  2023-03-31
29  30            批发和零售业   0.90    2635.429240  2023-03-31
30  31              房地产业   0.86    2519.415738  2023-03-31
31  32               建筑业   0.24     708.283312  2023-03-31
32  33       交通运输、仓储和邮政业   0.24     699.449400  2023-03-31
33  34         文化、体育和娱乐业   0.23     669.061400  2023-03-31
34  35           卫生和社会工作   0.20     596.362379  2023-03-31
35  36  电力、热力、燃气及水生产和供应业   0.01      36.160320  2023-03-31
36  37     水利、环境和公共设施管理业   0.00      10.346959  2023-03-31
```

## [AKShare](https://github.com/akfamily/akshare) 指数数据

### A股股票指数

#### 历史行情数据

##### 历史行情数据-东方财富

接口: stock_zh_index_daily_em

目标地址: http://quote.eastmoney.com/center/hszs.html

描述: 东方财富股票指数数据, 历史数据按日频率更新

限量: 单次返回具体指数的所有历史行情数据

输入参数

| 名称         | 类型  | 描述                                                                      |
|------------|-----|-------------------------------------------------------------------------|
| symbol     | str | symbol="sz399552"; 支持 sz: 深交所, sh: 上交所, bj: 北交所, csi: 中证指数 + id(000905) |
| start_date | str | start_date="19900101"                                                   |
| end_date   | str | end_date="20500101"                                                     |

输出参数

| 名称     | 类型      | 描述                    |
|--------|---------|-----------------------|
| date   | object  | 东方财富的数据开始时间, 不是证券上市时间 |
| open   | float64 | -                     |
| close  | float64 | -                     |
| high   | float64 | -                     |
| low    | float64 | -                     |
| volume | int64   | -                     |
| amount | float64 | -                     |

接口示例

```python
import akshare as ak

stock_zh_index_daily_em_df = ak.stock_zh_index_daily_em(symbol="sz399812")
print(stock_zh_index_daily_em_df)
```

数据示例

```
            date     open    close     high      low    volume        amount
0     2005-01-04   996.03   989.56   996.03   986.46    675733  4.986503e+08
1     2005-01-05   989.87  1008.59  1011.29   989.46   1037894  9.068431e+08
2     2005-01-06  1008.88  1002.81  1008.88   999.76    779152  5.631133e+08
3     2005-01-07  1002.10  1004.06  1015.61   999.56    898377  7.554397e+08
4     2005-01-10  1002.63  1014.12  1014.12  1000.90    651187  5.609582e+08
          ...      ...      ...      ...      ...       ...           ...
4566  2023-10-23  5659.09  5590.27  5666.15  5563.09   7956295  1.752549e+10
4567  2023-10-24  5608.75  5692.22  5700.26  5590.94   8032521  1.902381e+10
4568  2023-10-25  5735.01  5713.71  5751.73  5713.65   8597481  2.057249e+10
4569  2023-10-26  5694.04  5749.56  5755.59  5684.16   8636096  2.021819e+10
4570  2023-10-27  5747.77  5952.02  5969.61  5741.26  11493696  3.220613e+10
[4571 rows x 7 columns]
```
### 全球指数

#### 全球指数-历史行情数据-东财

接口: index_global_hist_em

目标地址: https://quote.eastmoney.com/gb/zsUDI.html

描述: 东方财富网-行情中心-全球指数-历史行情数据

输入参数

| 名称     | 类型  | 描述                                               |
|--------|-----|--------------------------------------------------|
| symbol | str | symbol="美元指数"; 可以通过 ak.index_global_spot_em() 获取 |

输出参数

| 名称  | 类型      | 描述      |
|-----|---------|---------|
| 日期  | object  | -       |
| 代码  | object  | -       |
| 名称  | object  | -       |
| 今开  | float64 | -       |
| 最新价 | float64 | -       |
| 最高  | float64 | -       |
| 最低  | float64 | -       |
| 振幅  | float64 | 主要单位: % |

接口示例

```python
import akshare as ak

index_global_hist_em_df = ak.index_global_hist_em(symbol="美元指数")
print(index_global_hist_em_df)
```

数据示例

```
          日期   代码    名称     今开     最新价   最高     最低    振幅
0      1986-01-09  UDI  美元指数  124.18  123.21  124.71  122.91  0.00
1      1986-01-10  UDI  美元指数  123.98  124.16  124.27  123.46  0.66
2      1986-01-13  UDI  美元指数  124.82  124.47  125.21  124.23  0.79
3      1986-01-14  UDI  美元指数  124.75  124.67  124.91  124.38  0.43
4      1986-01-15  UDI  美元指数  124.64  124.30  124.64  124.07  0.46
...           ...  ...   ...     ...     ...     ...     ...   ...
10027  2025-03-03  UDI  美元指数  107.38  106.54  107.41  106.42  0.92
10028  2025-03-04  UDI  美元指数  106.55  105.55  106.66  105.52  1.07
10029  2025-03-05  UDI  美元指数  105.56  104.32  105.78  104.26  1.44
10030  2025-03-06  UDI  美元指数  104.34  104.20  104.39  103.74  0.62
10031  2025-03-07  UDI  美元指数  104.23  103.63  104.25  103.55  0.67
[10032 rows x 8 columns]
```
