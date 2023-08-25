"""Provides utility functions and classes for communication between processes"""
from copy import deepcopy
from selectors import DefaultSelector, EVENT_READ
import logging


class SocketHandler:
	def __init__(self, conn, *, recieving=True):
		self.conn = conn
		self.recieving = recieving
		if recieving:
			self.monitor = DefaultSelector()
			self.monitor.register(conn, EVENT_READ)
			self.previous = '\x074\x11\x062\x11\x01exception\x10\x01Update has not yet run\x10\x062\x11\x01exception\x10\x01Update has not yet run\x10\x062\x11\x01exception\x10\x01Update has not yet run\x10\x062\x11\x01exception\x10\x01Update has not yet run\x00'

	def write(self, msg: bytes):
		if self.recieving:
			raise NotImplementedError

		self.conn.sendall(len(msg).to_bytes(3, "big", signed=False) + msg)

	def read(self) -> str:
		if not self.recieving:
			raise NotImplementedError

		if not self.monitor.select(0):
			return self.previous

		while self.monitor.select(0):
			length = int.from_bytes(self.conn.recv(3), "big", signed=False)
			read = 0
			msg = b''
			while read < length:
				to_read = min(length - read, 2048)
				chunk = self.conn.recv(to_read)
				msg += chunk
				read += to_read

		self.previous = msg.decode()
		return deepcopy(self.previous)



value_keywords = {'\x01': str, '\x02': int, '\x03': bool, '\x04': bool, '\x05': float,
				  '\x06': dict, '\x07': list, '\x08': tuple, '\x0a': set}
collection_delims = {"\x06", "\x07", "\x08", "\x0a"}


def network_encode(to_encode):
	encode_type = type(to_encode)

	if encode_type == str:
		out = '\x01' + to_encode
		return (out + "\x00").encode()

	elif encode_type == int:
		out = '\x02' + str(to_encode)
		return (out + "\x00").encode()

	elif encode_type == bool:
		if to_encode:
			return "\x03\x00".encode()
		return "\x04\x00".encode()

	elif encode_type == dict:
		out_list = []
		for key, value in to_encode.items():
			encoded_key = network_encode(key)[:-1]
			encoded_value = network_encode(value)[:-1]
			out_list += [encoded_key, encoded_value]
		return b"\x06" + str(len(out_list)).encode() + b"\x11" + b"\x10".join(out_list) + b"\x00"

	elif encode_type == list:
		out_list = []
		for value in to_encode:
			encoded_value = network_encode(value)[:-1]
			out_list.append(encoded_value)
		return b"\x07" + str(len(out_list)).encode() + b"\x11" + b"\x10".join(out_list) + b"\x00"

	elif encode_type == tuple:
		out_list = []
		for value in to_encode:
			encoded_value = network_encode(value)[:-1]
			out_list.append(encoded_value)
		return b"\x08" + str(len(out_list)).encode() + b"\x11" + b"\x10".join(out_list) + b"\x00"

	elif encode_type == set:
		out_list = []
		for value in to_encode:
			encoded_value = network_encode(value)[:-1]
			out_list.append(encoded_value)
		return b"\x0a" + str(len(out_list)).encode() + b"\x11" + b"\x10".join(out_list) + b"\x00"


def network_decode(value: str):
	"""Recursively decodes strings to original data"""
	def internal_len(to_len) -> int:
		"""Recursively gets total length of collection including sub-collections"""
		if type(to_len) not in {dict, list, set, tuple} or len(to_len) == 0:
			return 1

		if type(to_len) == dict:
			to_len = to_len.items()

		counter = 0
		for i in to_len:
			counter += internal_len(i)
		return counter

	value_type = value_keywords[value[0]]

	if value_type in {list, tuple, set, dict}:
		data_chunks = value[value.index('\x11') + 1:].split('\x10')
		length = int(value.split('\x11')[0][1:])
		out = []
		i = 0
		ind = 0
		while i < length:   # Iterate length of collection
			if data_chunks[ind][0] in collection_delims:
				val = network_decode('\x10'.join(data_chunks[ind:]))
				ind += internal_len(val)
			else:
				val = network_decode(data_chunks[ind])
				ind += 1
			i += 1
			out.append(val)

		if value_type == dict:
			try:
				return {out[i]: out[i+1] for i in range(0, len(out), 2)}
			except TypeError:
				logging.warning('Error converting to dict, value %s | %s', out, value)
		return value_type(out)

	elif value_type == str:
		return value[1:].replace('\x00', '')

	elif value_type == int:
		return int(value[1:].replace('\x00', ''))

	elif value_type == bool:
		if value.replace('\x00', '') == '\x03':
			return True
		return False


# Unit tests for encoder/decoder, useful for future edits
if __name__ == '__main__':
	tests = \
	['hi',
	 'bye',
	 1,
	 2,
	 10023,
	 True,
	 False,
	 ['what', 'no', '1', 1, 'bye', 'pls'],
	 [['nothin', 'personal'], ['what', 'no'], 'yes'],
	 {1:2, 'hi': 'bye', 1:'hi', 2:'bye'},
	 [['more', ['nested']], ['lists'], 'because', 'tests'],
	 {('well', 'this'): 'is awkward', 'because': ['i', 'said', 'so']},
	 {'a', 'b', 'c', 1, 2, 3},
	 {'a':'', 'b':['a', '1']},
	 [{'exception': 'Getting data from server failed'}, {'exception': 'Getting data from server failed'},
	  {'exception': 'Getting data from server failed'}, {'exception': 'Getting data from server failed'}],
	 [{'exception': 'Getting data from server failed', 'xception': ('Getting data from server failed','test')},
	  {'exception': 'Getting data from server failed'}, {'exception': 'Getting data from server failed'}]]
	for test in tests:
		encoded = network_encode(test)
		decoded = network_decode(encoded.decode())
		print(test == decoded, '|', encoded, '|', decoded)
