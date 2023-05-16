from hoggit import get_hoggit
from limakilo import get_lk


# Easy interface for variable-like gets
def __getattr__(name):
	if name == 'gaw':
		return get_hoggit('gaw')
	elif name == 'pgaw':
		return get_hoggit('pgaw')
	elif name == 'lkeu':
		return get_lk('eu')
	elif name == 'lkna':
		return get_lk('na')
	else:
		raise AttributeError(f'Unknown attribute "{name}" in module "server_data"')
