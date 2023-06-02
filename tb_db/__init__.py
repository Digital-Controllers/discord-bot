from configs import configs
import pymysql


def connect_to_db() -> pymysql.Connection:
	"""Connects to database with info in configs and returns connection"""
	return pymysql.connect(host=configs.DBINFO['host'], user=configs.DBINFO['user'],
						   password=configs.DBINFO['password'], database=configs.DBINFO['database'])


def sql_op(sql_cmd: list[str] | str, args: list[tuple] | tuple,
		   fetch_all: bool = False)-> list[tuple[tuple]] | list[tuple] | tuple[tuple] | tuple:
	"""
	Takes SQL command(s), passes them to database, and returns output. Intended for simple SQL command(s)

	Args:
		sql_cmd | Command(s) to be passed to database, given in
			tuple[str(SQL), tuple(args)] format
		fetch_all | Whether the db should fetch one or all values
	Returns:
		out | List of tuples or tuple (depending on type of sql_cmd) of value(s) returned from database
	"""

	assert (type(sql_cmd), type(args)) in {(list, list), (str, tuple)}, 'sql_op arguments of wrong types'

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
