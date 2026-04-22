"""Sample script to download, parse, and save orderbooks for selected symbols

Example - Backfill from 4 days ago for 2 days:
```
python orderbook_bfill.py 4 2
```

"""

import os
import sys
import time
import zipfile
from pathlib import Path
from datetime import datetime, timedelta, UTC
from data import download_raw_orderbook
from data import parse_orderbook
from data import save_parsed_orderbook
from config import syms, raw_dir, tmp_dir, out_dir

# 1. Create directories if don't exist
Path(raw_dir).mkdir(parents=True, exist_ok=True)
Path(tmp_dir).mkdir(parents=True, exist_ok=True)
Path(out_dir).mkdir(parents=True, exist_ok=True)

# 2. Download period
# stars from x days ago, runs for y days
from_x_days_ago, for_y_days = (sys.argv + [2, 1])[1:3]
from_x_days_ago = int(from_x_days_ago)
for_y_days = int(for_y_days)

start = datetime.now(UTC) - timedelta(days=from_x_days_ago)
day_indices = list(range(for_y_days))

# 3. Process per date and symbol
ntotal = len(syms) * len(day_indices)
count = 0
for day_index in day_indices:	

	date = (start + timedelta(days=day_index)).strftime('%Y-%m-%d')

	for sym in syms:
		count += 1
		print(f'{count}/{ntotal} - downloading orderbook {date}, {sym}...', end='')
				
		# 4. Attempt pricessing
		try:
			zip_path = download_raw_orderbook(sym=sym, date=date)	

			# 5. Unzip raw (zip) file to get data (jsonl) file
			print(f'> parsing...', end='')

			with zipfile.ZipFile(zip_path, 'r') as zip_ref:
				zip_ref.extractall(tmp_dir)

			# 6. Parse orderbook
			fname = zip_path.split('/')[-1].replace('.zip','')
			fpath = os.path.join(tmp_dir, fname)
			ob = parse_orderbook(fpath)
			
			# 7. Save as parque
			print(f'> saving...', end='')
			ob2 = save_parsed_orderbook(ob, out_dir)
			print('done')

			# 8. Clean up
			os.remove(fpath)		

		except Exception as err:
			print('ERROR')
			print(err)

		# 9. pause
		time.sleep(.5)
