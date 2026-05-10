import os
import re
import requests
import polars as pl
from pathlib import Path
from config import raw_dir

def download_raw_orderbook(sym: str, date: str):
	"""Downloads the Order Book zip file.

	Sample filename:
	"2026-04-04_BTCUSDT_ob200.data.zip"
	
	:param sym: 'BTCUSDT'
	:param date: 'yyyy-mm-dd'
	:return: path/to/file
	"""
	# 1. zip_path
	zip_fname = f'{date}_{sym}_ob200.data.zip'

	# 2. URL
	url = f'https://quote-saver.bycsi.com/orderbook/spot/{sym}/{zip_fname}'
	
	# 3. Landing directory
	dir = f'{raw_dir}/hist/orderbook/spot/{sym}'

	# 4. Path
	zip_path = os.path.join(dir, zip_fname)

	# 5. Download (Streaming)
	chunk_size = 2**13 # ~8KB
	with requests.get(url, stream=True) as res:
		res.raise_for_status()

		# 6. Create directory
		Path(dir).mkdir(parents=True, exist_ok=True)

		# 7. Save
		with open(zip_path, 'wb') as f:
			for chunk in res.iter_content(chunk_size=chunk_size):
				_ = f.write(chunk)

	return zip_path
	

def parse_orderbook(fpath: str):
	"""Parses the orderbook JSONL data.

	`data` column is a struct, containing bids (`b`) and asks (`a`)
	  as Nx2 arrays of price (p) and quantity (q). 

	:param fpath: path/to/unzip-file like 'blob/tmp/2026-04-27_BTCUSDT_ob200.data'
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
	path = f'{out_dir}/hist/orderbook/spot/sym={sym}/year={year}/month={month}/day={day}'
	Path(path).mkdir(parents=True, exist_ok=True)
	fname = fpath.split('/')[-1] + '.parquet'
	ob.sink_parquet(f'{path}/{fname}', mkdir=True)
	return ob