from discord import Embed as _Embed
from discord.abc import GuildChannel as _GuildChannel
from discord.ext import tasks as _tasks
from time import time
import server_data as _server_data
import logging


server_dict = {'gaw': 'Hoggit - Georgia At War', 'pgaw': 'Hoggit - Persian Gulf At War',
			   'lkeu': 'Lima Kilo - Flashpoint Levant - EU', 'lkna': 'Lima Kilo - Flashpoint Levant - NA'}


class PlayersEmbed(_Embed):
	def __init__(self, server: str, player_data: list[tuple[str, str]]):
		super().__init__(title=f"Players on {server_dict[server]}", color=0x3EBBE7)
		self.set_author(name='Digital Controllers')
		self.set_thumbnail(url="https://raw.githubusercontent.com/Digital-Controllers/website/main/docs/assets/logo.png")
		self.add_field(name=f'{len([_ for _, state in player_data if state == "Opt in"])}'
							f'/{len([_ for _, __ in player_data])} players opted-in.', value='', inline=False)
		self.add_field(name='Players online:', value='\n'.join([username for username, _ in player_data]))
		self.add_field(name='Comm states:', value='\n'.join([state for _, state in player_data]))


class ServersEmbed(_Embed):
	@classmethod
	async def create(cls, channel: _GuildChannel):
		"""Effectively __init__, but avoiding dunder for async purposes"""
		assert channel is not None, "NoneType given instead of GuildChannel"

		self = ServersEmbed()
		self.set_author(name='Digital Controllers')
		self.set_thumbnail(
			url="https://raw.githubusercontent.com/Digital-Controllers/website/main/docs/assets/logo.png")
		self.set_footer(text="Want to add a new server to the embed? Propose it in #development or add a GitHub issue.")

		for server in server_dict.values():
			self.add_field(name=server, value=None, inline=False)

		self.message = await channel.send(embed=self)
		await self.update_embed()
		self.update_embed.start()

		return self

	def __init__(self):
		"""Only separated from create to utilize super() and init class variables"""
		super().__init__(title="DCS Server Information", description="Updated in real-time.", color=0x3EBBE7)
		self.message = None
		self.last_time = None

	async def delete(self):
		await self.message.delete()

	@_tasks.loop(seconds=120)
	async def update_embed(self):
		try:
			if self.last_time and (delta := time() - self.last_time) > 120:
				logging.warning('ServersEmbed update timer took %s seconds', delta)
			update_data = (('gaw', _server_data.gaw), ('pgaw', _server_data.pgaw),
						   ('lkeu', _server_data.lkeu), ('lkna', _server_data.lkna))
			for i in range(len(update_data)):
				server_name, server_info = update_data[i]
				message = ', '.join([value for key, value in server_info.items() if key not in {'players'}])
				self.set_field_at(i, name=server_dict[server_name], value=message, inline=False)
			await self.message.edit(embed=self)
			self.last_time = time()
		except Exception as err:
			logging.error(err)
