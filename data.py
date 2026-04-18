import os
import requests
from pathlib import Path


def download_raw_orderbook(sym: str, date: str):
	"""Downloads the Order Book zip file.

	Sample filename:
	"2026-04-04_BTCUSDT_ob200.data.zip"
	
	:param sym: 'BTCUSDT'
	:param date: 'yyyy-mm-dd'
	:return: tuple of result (True/False) and 
		msg (path/to/file if True, error message otherwise)
	"""
	try:
		# 1. URL
		url = f'https://quote-saver.bycsi.com/orderbook/spot/{sym}/{date}_{sym}_ob200.data.zip'
		
		# 2. Landing directory
		dir = f'blob/raw/orderbook/{sym}/{date}'

		# 3. Path
		fname = url.split('/')[-1]
		fpath = os.path.join(dir, fname)

		# 4. Download (Streaming)
		chunk_size = 2**13 # ~8KB
		with requests.get(url, stream=True) as res:
			res.raise_for_status()

			# 5. Create directory
			Path(dir).mkdir(parents=True, exist_ok=True)

			# 6. Save
			with open(fpath, 'wb') as f:
				for chunk in res.iter_content(chunk_size=chunk_size):
					_ = f.write(chunk)

		return True, fpath
	
	except Exception as err:
		return False, err
	
