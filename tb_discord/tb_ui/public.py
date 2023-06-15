from discord import ButtonStyle, Embed, Interaction, Message, Role
from discord.ui import Button, RoleSelect, View


__all__ = ['RoleButtonEmbed', 'RoleChoiceView', 'RolesView']


class EventEmbed(Embed):
	def __init__(self):
		super().__init__()


# ---------- Role UI Elements ----------


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
