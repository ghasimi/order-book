"""Methods to parse and store orderbook files.
"""

import re
import polars as pl
from pathlib import Path

def parse_orderbook(fpath: str):
	"""Parses the orderbook JSONL data.

	`data` column is a struct, containing bids (`b`) and asks (`a`)
	  as Nx2 arrays of price (p) and quantity (q). 

	:param fpath: e.g., 'blob/raw/orderbook/2026-04-04_BTCUSDT_ob200.data'
	:return: LazyFrame of clean orderbook
	"""
	# 1. Raw data
	ob = pl.scan_ndjson(fpath)

	# 2. Bids
	bids = ob.with_columns(
			b = pl.col('data').struct.field('b'),
			side=pl.lit('b'),
	).explode('b').with_columns(
		p = pl.col('b').list.get(0).cast(pl.Float64),
		q = pl.col('b').list.get(1).cast(pl.Float64),
	).drop(['data', 'b'])

	# 3. Asks
	asks = ob.with_columns(
			a = pl.col('data').struct.field('a'),
			side=pl.lit('a')
	).explode('a').with_columns(
		p = pl.col('a').list.get(0).cast(pl.Float64),
		q = pl.col('a').list.get(1).cast(pl.Float64),
	).drop(['data', 'a'])

	# 4. Stacked
	ob = pl.concat([bids, asks])\
		.with_columns(
			fpath=pl.lit(fpath),
		)

	return ob


def save_parsed_orderbook(ob: pl.LazyFrame, out_dir: str):
	"""Saves a parsed orderbook in partiotionaed parquet format.

	:param ob: orderbook (LazyFrame) from parse_orderbook()
	:param out_dir: target directory for parquet files
	:return: the enriched orderbook
	"""
	
	# 1. Info from fpath
	fpath = ob.select('fpath').head(1).collect().item()
	sym = re.findall(r'\_(.*)\_ob200', fpath)[0]
	date = re.findall(r'\d{4}-\d{2}-\d{2}', fpath)[0]
	year, month, day =  date.split('-')

	# 2. Enrich
	ob = (ob
		.rename({'ts':'t',})		
		.with_columns(dt=pl.from_epoch('t', time_unit='ms'))
		.with_row_index('rn', offset=1)
	)

	# 3. Save
	path = f'{out_dir}/year={year}/month={month}/day={day}/sym={sym}'
	Path(path).mkdir(parents=True, exist_ok=True)
	fname = fpath.split('/')[-1] + '.parquet'
	ob.sink_parquet(f'{path}/{fname}', mkdir=True)
	return ob