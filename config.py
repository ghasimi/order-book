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

syms = conf.get('syms')
