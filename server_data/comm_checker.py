from dotenv import load_dotenv
from os import getenv
from sys import argv
from pathlib import Path
import pymysql


def _connect_to_db() -> pymysql.Connection:
	""" Shell function to return a connection to database with variables in .env file """
	return pymysql.connect(host=getenv('DBIP'), user=getenv('DBUN'), password=getenv('DBPW'), database=getenv('DBNAME'))


def check_usernames(data_dict: dict) -> dict:
	"""
	Extracts usernames from server data, checks against opt in/out database, inserts database values, and returns server data
	Args:
		data_dict | dict | Data dictionary reutrned from hoggit.get_hoggit or limakilo.get_lk
	Returns:
		data_dict | dict | Data dictionary updated with database data
	"""
	usernames = data_dict['players']
	with _connect_to_db() as db_conn:
		with db_conn.cursor() as cursor:
			user_data = []
			for username in usernames:
				cursor.execute("SELECT comms FROM user_comms WHERE username = %s;", (username,))
				if comms_data := cursor.fetchone():
					user_data.append((username, comms_dict[comms_data[0]]))
				else:
					user_data.append((username, 'Unknown'))
	data_dict['players'] = user_data
	return data_dict


def log_user(username: str, state: bool):
	"""
	Logs a user as opt in or out in database
	Args:
		username | str | username of user
		state | bool | Whether they opted in (True) or opted out (False)
	Returns:
		None
	"""
	with _connect_to_db() as db_conn:
		with db_conn.cursor() as cursor:
			cursor.execute("SELECT * FROM user_comms WHERE username = %s;", (username,))
			if cursor.fetchone():
				cursor.execute("UPDATE user_comms SET comms = %s WHERE username = %s;", (int(state), username))
			else:
				cursor.execute("INSERT INTO user_comms(username, comms) VALUES (%s, %s);", (username, int(state)))
			db_conn.commit()


load_dotenv(Path(__file__).parent / '../.env')
comms_dict = {0: 'Opt out', 1: 'Opt in'}


# Set up table if it doesn't exist
with _connect_to_db() as db_conn:
	with db_conn.cursor() as cursor:
		cursor.execute("CREATE TABLE IF NOT EXISTS user_comms("
					   "username VARCHAR(25) NOT NULL,"
					   "comms TINYINT(1) NOT NULL,"
					   "PRIMARY KEY (username));")
		db_conn.commit()


# Manual table debugging and management
if __name__ == '__main__':
	if '--show-table' in argv:
		with _connect_to_db() as db_conn:
			with db_conn.cursor() as cursor:
				cursor.execute("SELECT * FROM user_comms")
				print(cursor.fetchall())

	if '--reset-table' in argv:
		with _connect_to_db() as db_conn:
			with db_conn.cursor() as cursor:
				cursor.execute("CREATE OR REPLACE TABLE user_comms("
							   "username VARCHAR(25) NOT NULL,"
							   "comms TINYINT(1) NOT NULL,"
							   "PRIMARY KEY (username));")
				db_conn.commit()
