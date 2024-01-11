from configs import configs
from sys import argv
from typing import Callable
import pymysql


def connect_to_db() -> pymysql.Connection:
	"""Connects to database with info in configs and returns connection"""
	return pymysql.connect(host=configs.DBINFO["host"], user=configs.DBINFO["user"],
						   password=configs.DBINFO["password"], database=configs.DBINFO["database"])


def sql_func(func: Callable) -> Callable:
	"""Decorator for functions to be run in sql"""
	def wrapper(*args, **kwargs):
		with connect_to_db() as conn:
			with conn.cursor() as cursor:
				func(conn, cursor, *args, **kwargs)
	return wrapper


def sql_op(sql_cmd: list[str] | str, args: list[tuple] | tuple,
		   fetch_all: bool = False) -> list[tuple[tuple]] | list[tuple] | tuple[tuple] | tuple:
	"""
	Takes SQL command(s), passes them to database, and returns output. Intended for simple SQL command(s)

	Args:
		sql_cmd | Command(s) to be passed to database
		args | Arguments for sql_cmd(s), accepts empty tuple if none apply
		fetch_all | Whether the db should fetch one or all values
	Returns:
		out | List of tuples or tuple (depending on type of sql_cmd) of value(s) returned from database
	"""

	assert (type(sql_cmd), type(args)) in {(list, list), (str, tuple)}, "sql_op arguments of wrong types"

	with connect_to_db() as conn:
		with conn.cursor() as cursor:
			if type(sql_cmd) == list:
				out = []
				for cmd, arg in zip(sql_cmd, args):
					cursor.execute(cmd, args=arg)
					if fetch_all:
						out.append(cursor.fetchall())
					else:
						out.append(cursor.fetchone())
			else:
				cursor.execute(sql_cmd, args)
				if fetch_all:
					out = cursor.fetchall()
				else:
					out = cursor.fetchone()
		conn.commit()
	return out


if "-r" in argv:
	sql_op(["CREATE OR REPLACE TABLE user_comms("
				"username VARCHAR(25) PRIMARY KEY,"
				"comms TINYINT(1) NOT NULL);",
			"CREATE OR REPLACE TABLE persistent_messages("
				"message_id BIGINT UNSIGNED PRIMARY KEY,"
				"channel_id BIGINT UNSIGNED NOT NULL,"
				"type TINYINT NOT NULL,"
				"data TEXT);",
			"CREATE OR REPLACE TABLE students("
				"uid BIGINT UNSIGNED PRIMARY KEY,"
				"requests BLOB DEFAULT '',"
				"attended_sessions BLOB DEFAULT '',"
				"completed_sessions BLOB DEFAULT '');",
			"CREATE OR REPLACE TABLE server_data("
				"id TINYINT UNSIGNED PRIMARY KEY,"
				"data BLOB DEFAULT '');",
			"INSERT INTO server_data VALUES (0, %s);"], [(), (), (), (), (int(0).to_bytes(2, "big") * 256)])
	print(*sql_op(["SELECT * FROM user_comms;", "SELECT * FROM persistent_messages;", "SELECT * FROM students",
				  "SELECT * FROM server_data"], [(), (), (), ()], fetch_all=True), sep="\n")
else:
	sql_op(["CREATE TABLE IF NOT EXISTS user_comms("
				"username VARCHAR(25) PRIMARY KEY,"
				"comms TINYINT(1) NOT NULL);",
			"CREATE TABLE IF NOT EXISTS persistent_messages("
				"message_id BIGINT UNSIGNED PRIMARY KEY,"
				"channel_id BIGINT UNSIGNED NOT NULL,"
				"type TINYINT NOT NULL,"
				"data TEXT);",
			"CREATE TABLE IF NOT EXISTS students("
				"uid BIGINT UNSIGNED PRIMARY KEY,"
				"requests BLOB DEFAULT '',"
				"attended_sessions BLOB DEFAULT '',"
				"completed_sessions BLOB DEFAULT '');",
			"CREATE TABLE IF NOT EXISTS server_data("
				"id TINYINT UNSIGNED PRIMARY KEY,"
				"data BLOB DEFAULT '');"], [(), (), (), ()])

