# Order Book Ticker

Limit Order Book (LOB) tick data processing.

## Motivations

* Signal generation from Limit Order Book (LOB) 
* Scalable techniques to handle large and complex datasets

## Progress

* 2026-04-20: `bfill.py` downloads and parses historical LOB files and makes them accessible as `parquet`
* 2026-04-25: benchmarked query performance using Python `polars` and `kdb+/q`

## Definitions

* `Bid`: The highest price a buyer is willing to pay
* `Ask`: The lowest price a seller is willing to accept
* `Market order`: An order to buy or sell at the current market price
* `Limit order`: An order to buy at or lower than a specific price, OR sell at or higher than a specific price
* `Limit Order Book (LOB)`: A queue system for `limit orders` where priority is based on price and then arrival time, or price-visibility-time if hidden orders is an option
* `Polars`: An open-source library to work with large datasets ([Pola.rs](https://pola.rs)), also known as "fast pandas" due to the similarity of its API to tge popular library `Pandas` library

## Overview of LOB Data

* Source of current LOB data is ByBit.com
* Historical data that the code downloads are accessible at https://www.bybit.com/derivatives/en/history-data
* LOB files are in zipped files, named as `<yyyy-mm-dd>_<symbol>_ob200.data.zip` where `ob200` stands for 200-level orderbook, i.e. max of 200 price-quanity for each bid/ask leg
* LOB files are `JSON Line (JSONL)`, where each line is a `JSON` object; for example:

```
{"topic": "orderbook.200.XRPUSDT", "ts": 1776701658172, "type": "snapshot", "data": {"s": "XRPUSDT", "b": [["1.4277", "12480.06"], ... ["1.4061", "979.58"]], "a": [["1.4278", "5226.89"], ... ["1.4487", "28.95"]], "u": 15908117, "seq": 181025905987}, "cts": 1776701658157}
```

* That line can be deserialized to a Python dictionary:

```py
{
  "topic": "orderbook.200.XRPUSDT",
  "ts": 1776701658172,
  "type": "snapshot",
  "data": {
    "s": "XRPUSDT",
    "b": [
      [
        "1.4277",
        "12480.06"
      ],
		# ... truncated ...
      [
        "1.4061",
        "979.58"
      ]
    ],
    "a": [
      [
        "1.4278",
        "5226.89"
      ],
		# ... truncated ...
      [
        "1.4487",
        "28.95"
      ]
    ],
    "u": 15908117,
    "seq": 181025905987
  },
  "cts": 1776701658157
}
```

* Key fields:
	* `ts`: timestamp of the message in millseconds (ms)
	* `type`: there are two types:
		* `snapshot`:  complete states of LOB (i.e. all price levels up to the limit of the message's spec like 200 in this case)
		* `delta`: smaller messages to update quanity for an existing price level in LOB, or remove it, or add a new price level to the LOB	
	* `data`: which includes symbol `s`, bids `b`, asks `a`, while each bid and ask data are n x 2 arrays of price (1st column) and quantity (2nd column)
	* `cts`: timestamp of creation of this orderbook by the matching engine which, according to ByBit, can be correlated with trade data (another stream)

* The challenge here is to efficiently parse and store massive volumes of such messages and make them ready for other applications like signal generation or backtesting

## Pipeline Architecture

## Ingestion

* `config.py`: Specifies symbpls list and input/output directories, with the option to read from a `config.yml` file
* `bfill.py`: Downloads and parses LOB files and saves clean outputs as `parquet`
* The diagram shows LOB data strcuture and processing steps:

![Processing of LOB data](assets/diag-ob-data-process.drawio.png)

For example:

* Custom backfill, starting from 7 days ago for a 3-day period: `python bfill.py 7 3`
* Daily backfill, by scheduling `python bfill 1 1`

### Query

Tick data needs an optimized query engine. To get a sense of performance, I benchmarked `polars` and `kdb+/q` (community edition) where each query rebuilds the orderbook as of a certain timestamp, using `snapshot` and `delta` messages. `polars` directly uses the `parquet` files, while for `kdb+/q` I set up a standard `hdb` (Historical DB).

![polars vs kdb+/q query performance](./assets/polars-vs-kdb-q.png)

## Limitations

The focus was on exploring tick-level LOB data, not on optimization. For example, raw files of historical data are intentially downloaded with a short pause between HTTP calls to access resources gently.  

## Disclaimer

This is a personal project with educational purpose, and despite all attemps there is no guarantee on the correctness or complteness of content. Use of or reference to any name, link, source, vendor, software, broker, or instrument (e.g. coin) is NOT an endorsement or advice of any kind. Many of such choices were made randomly or for convenience of test/demo. For any copyrighted or licensed material or software you need to consult with the source or author. No part of this repo constitutes as financial advice or consultancy of any kind, implicitly or explicity, and you need to seek independent advice.