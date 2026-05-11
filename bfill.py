"""Sample script to download, parse, and save orderbooks for selected symbols

Example - Backfill spot data from 4 days ago for 2 days:
```
python bfill.py 4 2 spot
```

"""

import os
import sys
import time
import zipfile
from pathlib import Path
from datetime import datetime, timedelta, UTC
from data import Product
from data import download_raw_orderbook
from data import parse_orderbook
from data import save_parsed_orderbook
from config import syms, raw_dir, tmp_dir, out_dir

# 1. Download period
# stars from x days ago, runs for y days
from_x_days_ago, for_y_days, product_name = (sys.argv + [2, 1, 'spot'])[1:4]
from_x_days_ago = int(from_x_days_ago)
for_y_days = int(for_y_days)
pname = product_name.lower()
product = Product[pname.upper()]

start = datetime.now(UTC) - timedelta(days=from_x_days_ago)
day_indices = list(range(for_y_days))

# 2. Process per date and symbol
ntotal = len(syms) * len(day_indices)
count = 0
for day_index in day_indices:	

	date = (start + timedelta(days=day_index)).strftime('%Y-%m-%d')

	for sym in syms:
		count += 1
		print(f'{count}/{ntotal} - downloading orderbook/{pname} {date}, {sym}...', end='')
				
		# 3. Attempt pricessing
		try:
			zip_path = download_raw_orderbook(sym=sym, date=date, product=product)	

			# 4. Unzip raw (zip) file to get data (jsonl) file
			print(f'> unzip/parsing...', end='')
			unzip_dir = f'{tmp_dir}/orderbook/{pname}/{sym}/{date}'
			Path(unzip_dir).mkdir(parents=True, exist_ok=True)
			with zipfile.ZipFile(zip_path, 'r') as zip_ref:
				zip_ref.extractall(unzip_dir)

			# 5. Parse orderbook			
			fname = zip_path.split('/')[-1].replace('.zip','')
			fpath = f'{unzip_dir}/{fname}'
			ob = parse_orderbook(unzip_dir)
			
			# 6. Save as parque
			print(f'> saving...', end='')
			ob2 = save_parsed_orderbook(ob, sym, date, product)
			print('done')

			# 87. Clean up
			os.remove(fpath)		

		except Exception as err:
			print('ERROR')
			print(err)

		# 9. pause
		time.sleep(.5)
