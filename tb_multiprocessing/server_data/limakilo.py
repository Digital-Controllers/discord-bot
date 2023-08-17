from datetime import datetime, timedelta
from json import loads
from typing import Literal
from urllib.request import urlopen

from discord.utils import format_dt as dt


def get_lk(server: Literal["eu", "na"]) -> dict:
	with urlopen(f"https://levant.{server}.limakilo.net/status/data", timeout=30) as pipe:
		response = pipe.read().decode("utf-8")
	data_dict = loads(response)

	if data_dict is None:
		return {"exception": "Server offline"}

	seconds_to_restart = timedelta(seconds=int(data_dict["restartPeriod"]) - int(data_dict["modelTime"]))
	restart_time = dt((datetime.fromisoformat(data_dict['date'][:-1]) + seconds_to_restart), style="R")
	return {"player_count": f"{int(data_dict['players']['current']) - 1} player(s) online",
			"players": [i["name"] for i in data_dict["players"]['list']],
			"restart": f"restart {restart_time}"}
