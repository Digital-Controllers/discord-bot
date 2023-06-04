from tb_db import sql_func, sql_op


__all__ = ['check_usernames', 'log_user']


def check_usernames(data_dict: dict) -> dict:
	"""
	Extracts usernames from server data, checks against opt in/out database, inserts database values, and returns server data
	Args:
		data_dict | dict | Data dictionary reutrned from hoggit.get_hoggit or limakilo.get_lk
	Returns:
		data_dict | dict | Data dictionary updated with database data
	"""
	# Catches any server exceptions without wasting bandwidth and slowing processing
	if 'exception' in data_dict.keys():
		return data_dict

	usernames = data_dict['players']
	player_states = sql_op(["SELECT comms FROM user_comms WHERE username = %s;"] * len(usernames),
						   [(uname,) for uname in usernames])
	user_data = [(uname, comms_dict[comms_data]) for uname, comms_data in zip(usernames, player_states)]

	data_dict['players'] = user_data
	return data_dict


@sql_func
def log_user(db_conn, cursor, username: str, state: bool):
	"""
	Logs a user as opt in or out in database
	Args:
		username | str | username of user
		state | bool | Whether they opted in (True) or opted out (False)
	Returns:
		None
	"""
	cursor.execute("SELECT * FROM user_comms WHERE username = %s;", (username,))
	if cursor.fetchone():
		cursor.execute("UPDATE user_comms SET comms = %s WHERE username = %s;", (int(state), username))
	else:
		cursor.execute("INSERT INTO user_comms(username, comms) VALUES (%s, %s);", (username, int(state)))
	db_conn.commit()


comms_dict = {(0,): 'Opted out', (1,): 'Opted in', None: 'Unknown'}

# Set up table if it doesn't exist
sql_op("CREATE TABLE IF NOT EXISTS user_comms("
		"username VARCHAR(25) NOT NULL,"
		"comms TINYINT(1) NOT NULL,"
		"PRIMARY KEY (username));", ())
