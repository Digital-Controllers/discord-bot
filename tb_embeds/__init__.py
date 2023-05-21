from discord import Embed as _Embed


server_dict = {'gaw': 'Hoggit - Georgia At War', 'pgaw': 'Hoggit - Persian Gulf At War',
			   'lkeu': 'Lima Kilo - Flashpoint Levant - EU', 'lkna': 'Lima Kilo - Flashpoint Levant - NA'}


class PlayersEmbed(_Embed):
	def __init__(self, server: str, player_data: list[tuple[str, str]]):
		super().__init__(title=f"Players on {server_dict[server]}", color=0x3EBBE7)
		out_value = '\n'.join([': '.join([username, state]) for username, state in player_data])
		self.add_field(name='Players online:', value='\n'.join([username for username, _ in player_data]))
		self.add_field(name='Comm states::', value='\n'.join([state for _, state in player_data]))
