from datetime import datetime, timedelta
from discord import app_commands, Message, Interaction, TextChannel, utils
from tb_db import sql_op
from tb_discord.tb_ui import RoleButtonEmbed, RolesView, RoleChoiceView, RoleDeleteView
from tb_discord.data_structures import RolesMessage, role_messages


__all__ = ['command_list']


@app_commands.command()
async def create_role_buttons(interaction: Interaction, channel: TextChannel, message_id: int = None):
	# Get original message
	if message_id:
		message: Message = await channel.fetch_message(message_id)
	else:
		message = await utils.get(
			channel.history(limit=50, after=datetime.now() - timedelta(hours=1), oldest_first=False), author=interaction.user)
		if not message:
			await interaction.response.send_message(f'Your message in {channel.name} could not be found')
			return

	# Set up roles
	choice_view = RoleChoiceView(message)
	await interaction.response.send_message(view=choice_view, ephemeral=True)
	await choice_view.wait()
	roles = choice_view.roles.values

	# Send role message, log to db, and clean up
	out_message = await channel.send(message.content, embeds=message.embeds, view=RolesView(roles))
	sql_op('INSERT INTO role_messages(message_id, channel_id, roles) VALUES(%s, %s, %s);',
		   (out_message.id, out_message.channel.id, ''.join([str(value.id).zfill(20) for value in roles])))
	role_messages.append(RolesMessage(out_message, roles))
	await message.delete()
	await interaction.delete_original_response()


@app_commands.command()
async def list_role_buttons(interaction: Interaction):
	guild_messages = tuple(filter(lambda x: x.message.guild.id == interaction.guild.id, role_messages))
	await interaction.response.send_message(embed=RoleButtonEmbed(guild_messages))


@app_commands.command()
async def delete_role_buttons(interaction: Interaction):
	guild_messages = tuple(filter(lambda x: x.message.guild.id == interaction.guild.id, role_messages))
	embed = RoleButtonEmbed(guild_messages)
	buttons = RoleDeleteView(guild_messages)
	await interaction.response.send_message(embed=embed, view=buttons, ephemeral=True)


command_list = [create_role_buttons, delete_role_buttons, list_role_buttons]
