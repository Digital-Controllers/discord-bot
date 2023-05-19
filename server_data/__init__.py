from .comm_checker import check_usernames as _check_usernames, log_user as _log_user
from .hoggit import get_hoggit as _get_hoggit
from .limakilo import get_lk as _get_lk


def log_user(username: str, state: bool):
	_log_user(username, state)


# Easy interface for variable-like gets
def __getattr__(name):
	if name == 'gaw':
		return _check_usernames(_get_hoggit('gaw'))
	elif name == 'pgaw':
		return _check_usernames(_get_hoggit('pgaw'))
	elif name == 'lkeu':
		return _check_usernames(_get_lk('eu'))
	elif name == 'lkna':
		return _check_usernames(_get_lk('na'))
	else:
		raise AttributeError(f'Unknown attribute "{name}" in module "server_data"')
