import os
import re
import requests
import polars as pl
from polars import Schema, String, Int64, List, Struct
from pathlib import Path
from config import raw_dir, out_dir
from enum import Enum

orderbook_schema = Schema([('topic', String),
	('ts', Int64),
	('type', String),
	('id', String),
	('data',
		Struct({
		's': String, 
		'b': List(List(String)), 
		'a': List(List(String)), 
		'u': Int64, 
		'seq': Int64})),
	('cts', Int64)])


class Product(Enum):
	SPOT = 1
	LINEAR = 2
	OPTION = 3

def get_zip_fname(sym: str, date: str, product=Product):
	"""Downloadble archive's name"""
	if product.name == 'OPTION':
		coin = sym.replace('USDT','')
		return f'{date}_{coin}_USDT.ob25.zip'
	
	elif product.name in ['SPOT', 'LINEAR']:
		return f'{date}_{sym}_ob200.data.zip' 		

def download_raw_orderbook(sym: str, date: str, product=Product.SPOT):
	"""Downloads the Order Book zip file.

	Sample filename:
	"2026-04-04_BTCUSDT_ob200.data.zip"
	
	:param sym: 'BTCUSDT'
	:param date: 'yyyy-mm-dd'
	:param product: Product Enum (SPOT, LINEAR, OPTION)
	:return: path/to/file
	"""

	# 1. Info for URL and landing path
	zip_fname = get_zip_fname(sym, date, product)
	pname = product.name.lower()
	
	# 2. URL
	if product == Product.OPTION:
		coin = sym.replace('USDT','')
		url = f'https://quote-saver.bycsi.com/orderbook/{pname}/{coin}/{zip_fname}'
	else:
		url = f'https://quote-saver.bycsi.com/orderbook/{pname}/{sym}/{zip_fname}'
	
	# 3. Landing directory
	dir = f'{raw_dir}/hist/orderbook/{pname}/{sym}'

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
	ob = pl.scan_ndjson(fpath, schema=orderbook_schema)

	# 2. Bids
	bids = (
		ob.with_columns(
			b = pl.col('data').struct.field('b'),
			side=pl.lit('b'),
		)
		.explode('b')
		.with_columns(
			b = pl.col('b').fill_null([])
		)	
		.filter(
			pl.col('b').list.len() > 0
		)	
		.with_columns(
			p = pl.col('b').list.get(0).cast(pl.Float64),
			q = pl.col('b').list.get(1).cast(pl.Float64),
		)
		.drop(['data', 'b'])
	)


	# 3. Asks
	asks = (
		ob.with_columns(
				a = pl.col('data').struct.field('a'),
				side=pl.lit('a')
		)
		.explode('a')
		.with_columns(
			a = pl.col('a').fill_null([])
		)
		.filter(
			pl.col('a').list.len() > 0
		)
		.with_columns(
			p = pl.col('a').list.get(0).cast(pl.Float64),
			q = pl.col('a').list.get(1).cast(pl.Float64),
		)
		.drop(['data', 'a'])
		
	)

	# 4. Stacked
	ob = pl.concat([bids, asks])\
		.with_columns(
			fpath=pl.lit(fpath),
		)

	return ob


def save_parsed_orderbook(ob: pl.LazyFrame, sym:str, date:str, product=Product):
	"""Saves a parsed orderbook in partiotionaed parquet format.

	:param ob: orderbook (LazyFrame) from parse_orderbook()
	:return: path/to/parquet
	"""

	# 1. path 
	zip_fname = get_zip_fname(sym, date, product)
	fname = zip_fname.replace('.zip', '.parquet')
	pname = product.name.lower()
	year, month, day =  date.split('-')
	dir_ = f'{out_dir}/hist/orderbook/{pname}/sym={sym}/year={year}/month={month}/day={day}'
	path = f'{dir_}/{fname}'

	# 2. Save
	ob.sink_parquet(path, mkdir=True)
	return path