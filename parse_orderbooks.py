"""Sample script to parse orderbooks and save as parquet.
"""

import os
import re
import zipfile
from pathlib import Path
from orderbook_parser import parse_orderbook
from orderbook_parser import save_parsed_orderbook
from config import syms, raw_dir, tmp_dir, out_dir


# 1. Create directories if don't exist
Path(raw_dir).mkdir(parents=True, exist_ok=True)
Path(tmp_dir).mkdir(parents=True, exist_ok=True)
Path(out_dir).mkdir(parents=True, exist_ok=True)

# 2. Dates of raw (zip) files
dates = sorted([d for d in os.listdir(raw_dir)
		  if re.match(r'\d{4}-\d{2}-\d{2}', d)])

# 3. LIFO
for date in dates:

	# 4. Raw (zip) files
	zip_paths = sorted([f for f in os.listdir(f'{raw_dir}/{date}')
		   		if f.split('.')[-1] == 'zip'])
	
	for zip_path in zip_paths:

		# 5. Unzip raw (zip) file to get data (jsonl) file
		raw_path = f'blob/raw/orderbook/{date}/{zip_path}'
		print(f'parsing {raw_path}...', end='')

		with zipfile.ZipFile(raw_path, 'r') as zip_ref:
			zip_ref.extractall(tmp_dir)

		# 6. Parse orderbook
		fname = raw_path.split('/')[-1].replace('.zip','')
		fpath = os.path.join(tmp_dir, fname)
		ob = parse_orderbook(fpath)
		
		# 7. Save as parque
		ob2 = save_parsed_orderbook(ob, out_dir)

		# 8. Clean up
		os.remove(fpath)		
		print('done')