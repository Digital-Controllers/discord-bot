from .hoggit import get_hoggit as _get_hoggit
from .limakilo import get_lk as _get_lk


# Easy interface for variable-like gets
def __getattr__(name):
	if name == 'gaw':
		return _get_hoggit('gaw')
	elif name == 'pgaw':
		return _get_hoggit('pgaw')
	elif name == 'lkeu':
		return _get_lk('eu')
	elif name == 'lkna':
		return _get_lk('na')
	else:
		raise AttributeError(f'Unknown attribute "{name}" in module "server_data"')
