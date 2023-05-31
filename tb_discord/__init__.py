"""Coalesce all discord-related towerbot scripts"""
from discord.ext.commands import Bot
from discord import Intents

__all__ = ['bot']

bot = Bot(command_prefix='t?', intents=Intents.all())
bot.server_embed = None


# Imported below top to allow for bot to init
from tb_discord import tb_commands
import tb_discord.tb_events

for command in tb_commands.command_list:
	bot.tree.add_command(command)
