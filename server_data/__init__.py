from .comm_checker import check_usernames as _check_usernames, log_user
from .hoggit import get_hoggit as _get_hoggit
from .limakilo import get_lk as _get_lk
from time import sleep as _sleep, time as _time
from typing import Literal as _Literal
import threading
import logging


class LockVar:
	"""
	Variable with built-in threading.Lock

	Write and read value through .val property
	Supports boolean conversions
	"""
	def __init__(self, val):
		self._val = val
		self._lock = threading.Lock()
		self.changed = False

	@property
	def val(self):
		with self._lock:
			return self._val

	@val.setter
	def val(self, value):
		with self._lock:
			self._val = value
		self.changed = True

	def __bool__(self) -> bool:
		with self._lock:
			return bool(self._val)


class ServersThread:
	def __init__(self):
		self.close = LockVar(False)
		self.gaw_data = LockVar({'exception': 'Getting data'})
		self.pgaw_data = LockVar({'exception': 'Getting data'})
		self.lkeu_data = LockVar({'exception': 'Getting data'})
		self.lkna_data = LockVar({'exception': 'Getting data'})

		self.thread = threading.Thread(target=self._loop, daemon=True)
		self.thread.start()

	def _loop(self):
		while not self.close:
			start = _time()
			for server, val in (('gaw', self.gaw_data), ('pgaw', self.pgaw_data),
								('lkeu', self.lkeu_data), ('lkna', self.lkna_data)):
				try:
					data = self._get_data(server)
				except Exception as err:
					if not val.changed:
						val.val = {'exception': 'Getting data from server failed'}
					logging.error('Exception in getting data from %s\n%s', server, err)
				else:
					val.val = data
			if (sleep_time := 120 - (_time() - start)) > 0:
				_sleep(sleep_time)

	@staticmethod
	def _get_data(server: _Literal['gaw', 'pgaw', 'lkeu', 'lkna']) -> dict:
		match server:
			case 'gaw':
				return _check_usernames(_get_hoggit('gaw'))
			case 'pgaw':
				return _check_usernames(_get_hoggit('pgaw'))
			case 'lkeu':
				return _check_usernames(_get_lk('eu'))
			case 'lkna':
				return _check_usernames(_get_lk('na'))


if __name__ != '__main__':

	self = ServersThread()

	# Easy interface for variable-like gets
	def __getattr__(name):
		if name == 'gaw':
			return self.gaw_data.val
		elif name == 'pgaw':
			return self.pgaw_data.val
		elif name == 'lkeu':
			return self.lkeu_data.val
		elif name == 'lkna':
			return self.lkna_data.val
		else:
			raise AttributeError(f'Unknown attribute "{name}" in module "server_data"')

