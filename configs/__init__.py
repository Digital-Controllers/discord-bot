"""Organize config files and present a single, conclusive source"""
from dotenv import load_dotenv
from os import getenv
from pathlib import Path
import json


__all__ = ['configs']


# Raised if something is wrong when we load the config file.
class ConfigurationFileException(Exception):
	pass


class _ConfigReader:
	def __init__(self):
		config_parent = Path(__file__).parent
		# check if we have a config.json, and that it's valid
		try:
			with open(config_parent / 'config.json') as fd:
				cfg = json.load(fd)

				if not isinstance(cfg, dict):
					raise ConfigurationFileException

				# check that the config values exist and are the correct types
				for key, type_ in {"OWNER_IDS": list}.items():
					if key not in cfg.keys():
						raise ConfigurationFileException
					if not isinstance(cfg[key], type_):
						raise ConfigurationFileException
				# assume that if the types are all correct, it's probably okay
		except (FileNotFoundError, json.JSONDecodeError, ConfigurationFileException) as e:
			# Something went wrong while loading the config - write an empty one to the file.
			print(f"{str(e)} while loading config.json, writing blank config")
			cfg = {
				"OWNER_IDS": [],
				"'DCEMBED_CHANNEL_ID'": 0
			}
			with open(config_parent / 'config.json', "w") as fd:
				json.dump(cfg, fd)

		load_dotenv(config_parent / '.env')

		self.owner_ids: list = cfg['OWNER_IDS']
		self.dc_embed_channel_id: int = cfg['DCEMBED_CHANNEL_ID']
		self.TOKEN: str = getenv('TOKEN')
		self.DBINFO: dict[str: str] = {'host': getenv('DBIP'), 'user': getenv('DBUN'),
					   'password': getenv('DBPW'), 'database': getenv('DBNAME')}


if __name__ != '__main__':
	configs = _ConfigReader()
