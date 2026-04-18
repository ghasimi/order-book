"""Sample script to download orderbooks for selected symbols
"""

import time
import sys
from datetime import datetime, timedelta, UTC
from data import download_raw_orderbook
from config import syms

# 1. Download from yesterday
end = datetime.now(UTC) - timedelta(days=1)

# 2. For the lookback period (days),
#    default to 1 day if not supplied via command line
lookback_days = (sys.argv + [1])[1]

# 3. Download per date and symbol
ntotal = len(syms) * lookback_days
count = 0
for days in range(lookback_days):	

	date = (end - timedelta(days=days)).strftime('%Y-%m-%d')

	for sym in syms:
		count += 1
		print(f'{count}/{ntotal} - downloading orderbook for {date}, {sym}...', end='')

		res, msg = download_raw_orderbook(sym=sym, date=date)	
		if res:print('OK')
		if not res:print('ERROR')
		print(msg)

		time.sleep(1.0)
