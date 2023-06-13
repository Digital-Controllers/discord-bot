from datetime import datetime, timedelta
from discord.ui import Button, RoleSelect, View
from discord import app_commands, ButtonStyle, Message, Interaction, Role, TextChannel, utils
from tb_db import sql_op

__all__ = ['command_list', 'RolesView']


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


@app_commands.command()
async def create_reaction_role(interaction: Interaction, channel: TextChannel, message_id: int = None):
	# Get original message
	if message_id:
		message: Message = await channel.fetch_message(message_id)
	else:
		message = await utils.get(
			channel.history(limit=50, after=datetime.now() - timedelta(hours=1)), author=interaction.user)
		if not message:
			await interaction.response.send_message(f'Your message in {channel.name} could not be found')
			return

	# Set up roles
	choice_view = RoleChoiceView(message)
	await interaction.response.send_message(view=choice_view, ephemeral=True)
	await choice_view.wait()
	roles = choice_view.roles.values

	# Send role message, log to db, and clean up
	out_message = channel.send(message.content, embeds=message.embeds, view=RolesView(roles))
	sql_op('INSERT INTO role_messages(message_id, channel_id, roles) VALUES(%s, %s, %s);',
		   (out_message.id, out_message.channel.id, ''.join([str(value.id).zfill(20) for value in roles])))
	await message.delete()
	await interaction.delete_original_response()


command_list = [create_reaction_role]
