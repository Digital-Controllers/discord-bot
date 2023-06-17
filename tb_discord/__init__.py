"""Coalesce all discord-related towerbot scripts"""
from discord.ext.commands import Bot
from discord import Intents

__all__ = ['bot']

intents = Intents.none()
intents.guilds = True
intents.members = True
intents.guild_messages = True

bot = Bot(command_prefix='t?', intents=intents)
bot.server_embed = None


# Imported below top to allow for bot to init
import tb_discord.tb_events
from tb_discord import tb_commands

for command in tb_commands.command_list:
	bot.tree.add_command(command)
