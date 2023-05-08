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
from PIL import Image, ImageDraw, ImageFont, ImageColor
import random

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
        "OWNER_IDS": []
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

JETS = ["F16", "F18", "F15", "F35", "F22", "A10", "F14", "MIR2"]
HOLDING_POINTS = ["A", "B", "C", "D"]
AERODROMES = ["UG5X", "UG24", "UGKO", "UGKS", "URKA", "URKN", "URMM", "URSS"]
RUNWAYS = ["22", "04"]
DEPARTURES = ["GAM1D", "PAL1D", "ARN1D", "TIB1D", "SOR1D", "RUD1D", "AGI1D", "DIB1D", "TUN1D", "NAL1D"]


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


@bot.event
async def on_member_join(member):
    time = str(datetime.now())
    strip_text = {
        "slot": f"{time[11:16]}",
        "squawk": f"{random.randint(0, 6)}{random.randint(0, 7)}{random.randint(0, 7)}{random.randint(0, 7)}",
        "callsign": f"{member.name.upper()[:4]}{random.randint(0, 9)}{random.randint(0, 9)}",
        "aircraft": f"{random.choice(JETS)}",
        "hold": f"{random.choice(HOLDING_POINTS)}",
        "aerodrome": f"{random.choice(AERODROMES)}",
        "runway": f"{random.choice(RUNWAYS)}",
        "departure": f"{random.choice(DEPARTURES)}"
    }
    strip = Image.open("strip_blank.png")
    font = ImageFont.truetype("consolas.ttf", 40)
    font_large = ImageFont.truetype("consolas.ttf", 70)
    d = ImageDraw.Draw(strip)
    d.text((67, 101), strip_text["slot"], font=font, fill=(0, 0, 0), anchor="mm")
    d.text((305, 101), strip_text["callsign"], font=font_large, fill=(0, 0, 0), anchor="lm")
    d.text((914, 101), strip_text["hold"], font=font_large, fill=(0, 0, 0), anchor="mm")
    d.text((1339, 150), strip_text["aerodrome"], font=font, fill=(0, 0, 0), anchor="mm")
    d.text((1632, 101), strip_text["runway"], font=font_large, fill=(0, 0, 0), anchor="mm")
    d.text((1803, 101), strip_text["departure"], font=font_large, fill=(0, 0, 0), anchor="mm")
    d.text((646, 150), strip_text["squawk"], font=font, fill=(0, 0, 0), anchor="lm")
    d.text((646, 57), "M/" + strip_text["aircraft"], font=font, fill=(0, 0, 0), anchor="lm")
    strip.save(fp="strip.png")
    await bot.get_channel(1099805424934469652).send(f"Welcome to Digital Controllers, {member.name}!", file=discord.File("strip.png"))
    os.remove("strip.png")

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
async def metar(interaction: discord.Interaction, airport: str, decode: str=None):
    #Split options into 2 different try/except statements to give better debug output if necessary
    
    if decode == None: #If user does not want the decoded METAR
        try:
            with urlopen(f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{airport.upper()}.TXT") as x:
                data = x.read().decode("utf-8")
            await interaction.response.send_message(f"```{data}```")
        except:
            await interaction.response.send_message(f"Failed to fetch default METAR.")
    else: #If user wants decoded METAR
        try:
            with urlopen(f"https://beta.aviationweather.gov/cgi-bin/data/metar.php?ids={airport.upper()}&format=decoded") as x:
                data = x.read().decode("utf-8")
            await interaction.response.send_message(f"```{data}```")
        except:
            await interaction.response.send_message(f"Failed to fetch decoded METAR.")

bot.tree.add_command(ping)
bot.tree.add_command(metar)
bot.run(TOKEN)
