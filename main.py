import logging
logging.basicConfig(filename='runtime.log', encoding='utf-8', level=logging.INFO)

from configs import configs
from datetime import datetime
from signal import signal, SIGINT
from tb_discord import bot
from tb_multiprocessing import stop_list


# =======INTERRUPT HANDLING=======


def clean_close(signum, frame):
	"""Prevents leaving hanging TCP sockets on localhost"""
	for func in stop_list:
		func()
	exit()


signal(SIGINT, clean_close)


# =======INIT=======

utc_start = datetime.utcnow()
print(f"Started at {str(utc_start)[:-16]}")
logging.info("Started on %s", utc_start.strftime("%d-%m-%Y at %H:%M:%S UTC%z"))

bot.run(configs.TOKEN)
