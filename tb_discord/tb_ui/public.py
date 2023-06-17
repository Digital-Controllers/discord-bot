from discord import ButtonStyle, Embed, Interaction, Message, Role
from discord.errors import NotFound
from discord.ui import Button, RoleSelect, View
from tb_db import sql_op
from tb_discord.data_structures import RolesMessage, role_messages
import logging


__all__ = ['RoleButtonEmbed', 'RoleChoiceView', 'RolesView', 'RoleDeleteView']


class EventEmbed(Embed):
	def __init__(self):
		super().__init__()


# ---------- Role UI Elements ----------


class RoleButtonEmbed(Embed):
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


class RoleDeleteView(View):
	def __init__(self, messages: tuple[RolesMessage]):
		super().__init__(timeout=120)
		if len(messages) > 25:
			logging.warning('User at guild %s (id %s) has more than 25 role messages',
			                messages[0].message.guild.name, messages[0].message.guild.id)
			messages = messages[:25]

		for message, i in zip(messages, range(len(messages))):
			self.add_item(RoleDeleteButton(message, i))


class RoleChoiceView(View):
	def __init__(self, message: Message):
		super().__init__(timeout=120)
		self.message = message
		self.roles = TBRolesSelect()
		self.add_item(self.roles)


class TBRolesSelect(RoleSelect):
	def __init__(self):
		super().__init__(min_values=1, max_values=10)

	async def callback(self, interaction: Interaction):
		self.view.stop()


class RolesView(View):
	def __init__(self, roles: list[Role]):
		super().__init__(timeout=None)
		for role in roles:
			self.add_item(RoleButton(role))


class RoleButton(Button):
	def __init__(self, role: Role):
		super().__init__(style=ButtonStyle.primary, label=role.name)
		self.role = role

	async def callback(self, interaction: Interaction):
		if self.role in interaction.user.roles:
			await interaction.user.remove_roles(self.role)
		else:
			await interaction.user.add_roles(self.role)
		await interaction.response.defer()


class RoleDeleteButton(Button):
	def __init__(self, role_msg: RolesMessage, ind: int):
		super().__init__(style=ButtonStyle.danger, label=f'Msg {ind + 1}', row=ind // 5)
		self.message = role_msg

	async def callback(self, interaction: Interaction):
		try:
			await self.message.message.delete()
		except NotFound:
			await interaction.response.send_message('Could not find requested message', ephemeral=True)
		else:
			await interaction.response.defer()

		try:
			role_messages.remove(self.message)
		except ValueError:
			# Catches repeat uses of the same button throwing an error
			pass
		else:
			sql_op('DELETE FROM role_messages WHERE message_id = %s', (self.message.message.id,))

