"""Creates multiprocessing processes for server_data with minimal dependancies"""
from comm_checker import check_usernames
from hoggit import get_hoggit
from limakilo import get_lk
from pathlib import Path
from signal import signal, SIGINT
from sys import path
from time import sleep, time
import logging
import socket

# Path hack, but I'd otherwise have to make this subprocess above the main in the directory structure.
path.append(str(Path(__file__).parent.parent))

from io_utils import network_encode, SocketHandler


logging.basicConfig(filename=Path(__file__).parent / 'runtime.log', encoding='utf-8', level=logging.INFO)


# =======INTERRUPT HANDLER=======


def interrupt_handler(signum, frame):
	print('Closing subprocess')
	sock.close()
	exit()


signal(SIGINT, interrupt_handler)


# =======PROCESS COMMUNICATION=======


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("localhost", 20250))
connection = SocketHandler(sock, recieving=False)


# =======MAIN LOOP=======


while True:
	start = time()
	data = [{'exception': 'Getting data from server failed'}, {'exception': 'Getting data from server failed'},
			{'exception': 'Getting data from server failed'}, {'exception': 'Getting data from server failed'}]
	for server, ind in (('gaw', 0), ('pgaw', 1), ('lkeu', 2), ('lkna', 3)):
		try:
			match server:
				case 'gaw':
					data[ind] = check_usernames(get_hoggit('gaw'))
				case 'pgaw':
					data[ind] = check_usernames(get_hoggit('pgaw'))
				case 'lkeu':
					data[ind] = check_usernames(get_lk('eu'))
				case 'lkna':
					data[ind] = check_usernames(get_lk('na'))
		except Exception as err:
			logging.error('Exception in getting data from %s\n%s', server, err)
	connection.write(network_encode(data))
	sleep(120 - time() + start)


