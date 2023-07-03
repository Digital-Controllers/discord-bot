from collections import deque
from discord import ButtonStyle, Embed, Interaction, Message, Role, TextChannel
from discord.errors import NotFound
from discord.ui import Button, RoleSelect, View
from tb_db import sql_op
import logging


__all__ = ['RolesMessage', 'RoleButtonEmbed', 'RoleChoiceView', 'RoleDeleteView']


class RolesMessage:
	"""Shell class for message object with role data attached, used to keep track of role button messages"""

	role_messages = deque()

	@classmethod
	async def find(cls, message: Message, channel: TextChannel, role_ids: str):
		"""Creates rolesmessage object based off of database data"""
		roles = [channel.guild.get_role(role_id) for role_id in (int(''.join(i)) for i in zip(*[iter(role_ids)]*20))]
		RolesMessage.role_messages.append(RolesMessage(await message.edit(view=RolesView(roles)), roles))

	@classmethod
	async def create(cls, message: Message, channel: TextChannel, roles: list[Role]):
		new_message = await channel.send(message.content, embeds=message.embeds, view=RolesView(roles))
		sql_op('INSERT INTO persistent_messages(message_id, channel_id, type, data) VALUES(%s, %s, %s, %s);',
		       (new_message.id, channel.id, 1, ''.join([str(value.id).zfill(20) for value in roles])))
		RolesMessage.role_messages.append(RolesMessage(message=new_message, roles=roles))
		await message.delete()

	def __init__(self, message: Message, roles: list[Role]):
		self.message = message
		self.roles = roles


class RoleButtonEmbed(Embed):
	"""Embed listing current role buttons"""
	def __init__(self, messages: tuple):
		super().__init__(title='Current role buttons', color=0x3EBBE7)
		self.set_author(name='Digital Controllers')
		self.set_thumbnail(url="https://raw.githubusercontent.com/Digital-Controllers/website/main/docs/assets/logo.png")

		lines = []
		for message, i in zip(messages, range(len(messages))):
			desc_str = f'{i + 1}) ' + message.message.content
			if len(desc_str) > 25:
				desc_str = desc_str[:22] + '...'
			lines.append(desc_str + '\n> ' + '\n> '.join([role.name for role in message.roles]))

		if not lines:
			lines = ['No role messages']

		self.add_field(name='Role messages:', value='\n\n'.join(lines))


# Creating role buttons

class RoleChoiceView(View):
	"""View containing a TBRolesSelect"""
	def __init__(self):
		super().__init__(timeout=120)
		self.roles = TBRolesSelect()
		self.add_item(self.roles)


class TBRolesSelect(RoleSelect):
	"""RoleSelect that stops parent view when closed"""
	def __init__(self):
		super().__init__(min_values=1, max_values=10)

	async def callback(self, interaction: Interaction):
		self.view.stop()


# Role button messages

class RolesView(View):
	"""View containing RoleButton(s) for a role button message"""
	def __init__(self, roles: list[Role]):
		super().__init__(timeout=None)
		for role in roles:
			self.add_item(RoleButton(role))


class RoleButton(Button):
	"""Button that assigns or removes role from clicking user"""
	def __init__(self, role: Role):
		super().__init__(style=ButtonStyle.primary, label=role.name)
		self.role = role

	async def callback(self, interaction: Interaction):
		if self.role in interaction.user.roles:
			await interaction.user.remove_roles(self.role)
		else:
			await interaction.user.add_roles(self.role)
		await interaction.response.defer()


# Deleting role button messages

class RoleDeleteView(View):
	"""View for deleting existing role buttons"""
	def __init__(self, messages: tuple[RolesMessage]):
		super().__init__(timeout=120)
		if len(messages) > 25:
			logging.warning('User at guild %s (id %s) has more than 25 role messages',
			                messages[0].message.guild.name, messages[0].message.guild.id)
			messages = messages[:25]

		for message, i in zip(messages, range(len(messages))):
			self.add_item(RoleDeleteButton(message, i))


class RoleDeleteButton(Button):
	"""Button to delete assigned RolesMessage"""
	def __init__(self, role_msg: RolesMessage, ind: int):
		super().__init__(style=ButtonStyle.danger, label=f'Msg {ind + 1}', row=ind // 5)
		self.message = role_msg

	async def callback(self, interaction: Interaction):
		try:
			await self.message.message.delete()
		except NotFound:
			await interaction.response.send_message('Could not find requested message', ephemeral=True)
		else:
			RolesMessage.role_messages.remove(self.message)
			sql_op('DELETE FROM role_messages WHERE message_id = %s', (self.message.message.id,))
			await interaction.response.defer()
