"""Module for ui elements based around DCS server data"""
from discord import Embed, Message, TextChannel
from discord.abc import GuildChannel
from discord.errors import NotFound
from discord.ext import tasks
from tb_db import sql_op
from time import time
import logging
import server_data


__all__ = ['PlayersEmbed', 'ServersEmbed']


server_dict = {'gaw': 'Hoggit - Georgia At War', 'pgaw': 'Hoggit - Persian Gulf At War',
			   'lkeu': 'Lima Kilo - Flashpoint Levant - EU', 'lkna': 'Lima Kilo - Flashpoint Levant - NA'}


class PlayersEmbed(Embed):
	def __init__(self, server: str, player_data: list[tuple[str, str]]):
		super().__init__(title=f"Players on {server_dict[server]}", color=0x3EBBE7)
		self.set_author(name='Digital Controllers')
		self.set_thumbnail(url="https://raw.githubusercontent.com/Digital-Controllers/website/main/docs/assets/logo.png")
		self.add_field(name=f'{len([_ for _, state in player_data if state == "Opt in"])}'
							f'/{len([_ for _, __ in player_data])} players opted-in.', value='', inline=False)
		self.add_field(name='Players online:', value='\n'.join([username for username, _ in player_data]))
		self.add_field(name='Comm states:', value='\n'.join([state for _, state in player_data]))


class ServersEmbed(Embed):

	active_embed = None

	@classmethod
	async def create(cls, channel: GuildChannel):
		"""Effectively __init__, but avoiding dunder for async purposes"""
		assert channel is not None, "NoneType given instead of GuildChannel"

		self = ServersEmbed()

		self.message = await channel.send(embed=self)
		await self.update_embed()
		self.update_embed.start()

		ServersEmbed.active_embed = self
		sql_op('INSERT INTO persistent_messages(message_id, channel_id, type, data) VALUES(%s, %s, %s, %s)',
		       (self.message.id, channel.id, 0, ''))

	@classmethod
	async def find(cls, message: Message, channel: TextChannel, data: str):
		"""Updates existing servers embed based off of database data"""
		self = ServersEmbed()
		self.message = await message.edit(embed=self)
		self.update_embed.start()
		ServersEmbed.active_embed = self

	def __init__(self):
		"""Only separated from create to utilize super() and init class variables"""
		super().__init__(title="DCS Server Information", description="Updated in real-time.", color=0x3EBBE7)

		self.set_author(name='Digital Controllers')
		self.set_thumbnail(
			url="https://raw.githubusercontent.com/Digital-Controllers/website/main/docs/assets/logo.png")
		self.set_footer(text="Want to add a new server to the embed? Propose it in #development or add a GitHub issue.")

		for server in server_dict.values():
			self.add_field(name=server, value=None, inline=False)

		self.message = None
		self.last_time = None

	async def delete(self):
		sql_op('DELETE FROM persistent_messages WHERE message_id = %s', (self.message.id,))
		await self.message.delete()
		ServersEmbed.active_embed = None

	@tasks.loop(seconds=120)
	async def update_embed(self):
		try:
			if self.last_time and (delta := time() - self.last_time) > 120:
				logging.warning('ServersEmbed update timer took %s seconds', delta)
			update_data = (('gaw', server_data.gaw), ('pgaw', server_data.pgaw),
			               ('lkeu', server_data.lkeu), ('lkna', server_data.lkna))
			for i in range(len(update_data)):
				server_name, server_info = update_data[i]
				message = ', '.join([value for key, value in server_info.items() if key not in {'players'}])
				self.set_field_at(i, name=server_dict[server_name], value=message, inline=False)
			await self.message.edit(embed=self)
			self.last_time = time()
		except NotFound:
			await self.delete()
		except Exception as err:
			logging.error(err)
