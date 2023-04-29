import os
import json
import sys
import time
from datetime import datetime, timezone
from urllib.request import urlopen
import discord
import discord.ext
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import tasks, commands
from dotenv import load_dotenv

sys.path.insert(0, "venv/Lib/site-packages")


# =======UTILITIES=======

# Raised if something is wrong when we load the config file.
class ConfigurationFileException(Exception):
    pass


# used in owner check
class AccessDeniedMessage(commands.CheckFailure):
    pass


# =======INIT=======

# check if we have a config.json, and that it's valid
try:
    with open("config.json") as fd:
        cfg = json.load(fd)

        if not isinstance(cfg, dict):
            raise ConfigurationFileException

        # check that the config values exist and are the correct types
        for key, type_ in {"OWNER_IDS": list}.items():
            if not key in cfg.keys():
                raise ConfigurationFileException
            if not isinstance(cfg[key], type_):
                raise ConfigurationFileException
            # assume that if the types are all correct, it's probably okay

except (FileNotFoundError, json.JSONDecodeError, ConfigurationFileException) as e:
    # Something went wrong while loading the config - write an empty one to the file.
    print(f"{str(e)} while loading config.json, writing blank config")
    cfg = {
        "OWNER_IDS": [331082223677734923]
    }
    with open("config.json", "w") as fd:
        json.dump(cfg, fd)

load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='t?', intents=intents)

print(f"Started at {str(datetime.now(timezone.utc))[:-16]}")


# usage:
# @bot.command()
# @check_is_owner()
# async def command(...):
# will automatically say "Failed owner check." on failure
def check_is_owner():
    def predicate(ctx):
        if not ctx.author.id in cfg["OWNER_IDS"]:
            raise AccessDeniedMessage("Failed owner check.")
        return True

    return commands.check(predicate)


# =======EVENTS AND LOOPS=======

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@bot.command()
@check_is_owner()
async def sync_command_tree(ctx):
    await bot.tree.sync()
    await ctx.reply(
        "Tree synced.")


@sync_command_tree.error
async def sync_command_tree_error(ctx, error):
    if isinstance(error, AccessDeniedMessage):
        await ctx.reply(error)


@app_commands.command()
async def ping(interaction: discord.Interaction):
    latency = str(bot.latency)[:-13]
    await interaction.response.send_message(f"Pong! Ping is {latency}s.")


@app_commands.command()
async def metar(interaction: discord.Interaction, airport: str):
    try:
        with urlopen(f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{airport.upper()}.TXT") as x:
            data = x.read().decode("utf-8")
        await interaction.response.send_message(f"```{data}```")
    except:
        await interaction.response.send_message(f"METAR failed. Try again, maybe?")

bot.tree.add_command(ping)
bot.tree.add_command(metar)
bot.run(TOKEN)
