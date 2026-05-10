import yaml

with open('config.yml', 'r') as f:
	"""
	Example of listing symbols in the YAML file:

	syms:
		- BTCUSDT
		- ETHUSDT
		- SOLUSDT		
	"""
	conf = yaml.safe_load(f)

# Symbols
syms = conf.get('syms', [])

# Raw data directory
raw_dir = conf.get('raw_dir', 'blob/raw')

# Temp (staging) directory
tmp_dir = conf.get('tmp_dir', 'blob/tmp')

# Output directory
out_dir = conf.get('out_dir', 'blob/out')

