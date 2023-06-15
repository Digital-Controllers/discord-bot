from discord import Embed
from tb_discord.data_structures import RolesMessage


__all__ = ['RoleButtonEmbed']


class EventEmbed(Embed):
	def __init__(self):
		super().__init__()


class RoleButtonEmbed(Embed):
	def __init__(self, messages: filter):
		super().__init__(title='Current role buttons', color=0x3EBBE7)
		self.set_author(name='Digital Controllers')
		self.set_thumbnail(url="https://raw.githubusercontent.com/Digital-Controllers/website/main/docs/assets/logo.png")

		lines = []
		for message in messages:
			if len(desc_str := message.message.content) > 25:
				desc_str = desc_str[:18] + '...'
			lines.append(desc_str + '\n> ' + '\n> '.join([role.name for role in message.roles]))

		if not lines:
			lines = ['No role messages']

		self.add_field(name='Role messages:', value='\n\n'.join(lines))


