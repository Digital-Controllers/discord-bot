from datetime import datetime, timedelta
from json import loads
from re import match
from typing import Literal
from urllib.request import urlopen


def get_hoggit(server: Literal['gaw', 'pgaw']) -> dict:
    with urlopen(f'https://statecache.hoggitworld.com/{server}') as pipe:
        response = pipe.read().decode('utf-8')
    data_dict = loads(response)

    # Check data to be processed for unexpected types
    if (type(data_dict['objects']), type(data_dict['players']), type(data_dict['uptime'])) != (list, int, float) \
            or data_dict['updateTime'] == '':
        return {'exception': 'Unexpected data types in server information'}

    seconds_to_restart = timedelta(seconds=14400 - data_dict['uptime'])
    # List comprehension to end all list comprehensions (filters all except enemy air units with non-standard names)
    players = [v['Pilot'] for v in data_dict['objects'] if
               v['Coalition'] == 'Enemies' and v['Type'] in {'Air+FixedWing', 'Air+Rotorcraft'} and not match(
                   r'USA air \d+ unit\d', v['Pilot'])]

    return {'player_count': f"{data_dict['players'] - 1} player(s) online",
            'players': players,
            'metar': f"METAR: `{data_dict['metar']}`",
            'restart': f"restart <t:{round((datetime.fromisoformat(data_dict['updateTime']) + seconds_to_restart).timestamp())}:R>"}
