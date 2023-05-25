from datetime import datetime
from discord import app_commands, File, Intents, Interaction
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from urllib.request import urlopen
import json
import os
import random
import re
import server_data
import tb_embeds


# =======UTILITIES=======

# Raised if something is wrong when we load the config file.
class ConfigurationFileException(Exception):
    pass


# =======CONFIGS=======

# check if we have a config.json, and that it's valid
try:
    with open("config.json") as fd:
        cfg = json.load(fd)

        if not isinstance(cfg, dict):
            raise ConfigurationFileException

        # check that the config values exist and are the correct types
        for key, type_ in {"OWNER_IDS": list}.items():
            if key not in cfg.keys():
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


# =======INIT=======

bot = commands.Bot(command_prefix='t?', intents=Intents.all())

print(f"Started at {str(datetime.utcnow())[:-16]}")
bot.server_embed = None

JETS = ["F16", "F18", "F15", "F35", "F22", "A10", "F14", "MIR2"]
HOLDING_POINTS = ["A", "B", "C", "D"]
AERODROMES = ["UG5X", "UG24", "UGKO", "UGKS", "URKA", "URKN", "URMM", "URSS"]
RUNWAYS = ["22", "04"]
DEPARTURES = ["GAM1D", "PAL1D", "ARN1D", "TIB1D", "SOR1D", "RUD1D", "AGI1D", "DIB1D", "TUN1D", "NAL1D"]


def check_is_owner():
    """
    Checks if author of a message is registered as owner in config.json
    Usage:
        @bot.command()
        @check_is_owner()
        async def command(...):
        Commands with this check should not appear to any non-admin
    Returns:
        True or False | If owner is or is not in config
    """

    def predicate(interaction: Interaction):
        if interaction.user.id not in cfg["OWNER_IDS"]:  # May not be coroutine-safe in the future, fine for now
            return False
        return True

    return app_commands.check(predicate)


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
        "callsign": (f"{re.sub('[^a-zA-Z0-9]', '', member.name.upper())[:4]}" 
                     f"{random.randint(0, 9)}{random.randint(0, 9)}"),
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
    await bot.get_channel(1099805424934469652).send(f"Welcome to Digital Controllers, "
                                                    f"{member.name}!", file=File("strip.png"))
    os.remove("strip.png")


# =======APP COMMANDS=======


@app_commands.command()
@app_commands.describe(name="DCS server selection")
@app_commands.choices(name=[
    app_commands.Choice(name="Hoggit - Georgia At War", value="gaw"),
    app_commands.Choice(name="Hoggit - Persian Gulf At War", value="pgaw"),
    app_commands.Choice(name="Lima Kilo - Flashpoint Levant - EU", value="lkeu"),
    app_commands.Choice(name="Lima Kilo - Flashpoint Levant - NA", value="lkna")
])
async def info(interaction: Interaction, name: app_commands.Choice[str], details: str = 'all'):
    """
    Gets player count info for designated servers
    Args:
        name | Choice[str] | Name of server
        details | str | Wanted statistics, defaults to all
    """
    server = name.value  # take the actual string value from the input Choice
    details = details.lower()

    await interaction.response.send_message('Getting server data...')

    stats = server_data.__getattr__(server)

    if details == 'all':
        await interaction.edit_original_response(content=', '.join(
            [value for key, value in stats.items() if key not in {'players'}]))
    elif details == 'players':
        await interaction.edit_original_response(content='', embed=tb_embeds.PlayersEmbed(server, stats['players']))
    else:
        try:
            await interaction.edit_original_response(content=stats[details])
        except KeyError:
            await interaction.edit_original_response(content="Requested data isn't available for that server.")


@app_commands.command()
async def metar(interaction: Interaction, airport: str, decode: bool = False):
    # Split options into 2 different try/except statements to give better debug output if necessary
    if not decode:  # If user does not want the decoded METAR
        try:
            with urlopen(f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{airport.upper()}.TXT") as x:
                data = x.read().decode("utf-8")
            await interaction.response.send_message(f"```{data}```")
        except:
            await interaction.response.send_message(f"Failed to fetch default METAR.")
    else:  # If user wants decoded METAR
        try:
            with urlopen(
                    f"https://beta.aviationweather.gov/cgi-bin/data/metar.php?ids={airport.upper()}&format=decoded")\
                    as x:
                data = x.read().decode("utf-8")
                if not data:
                    raise ValueError("Response was empty.")
                else:
                    await interaction.response.send_message(f"```{data}```")
        except:
            await interaction.response.send_message("Failed to fetch decoded METAR.")


@app_commands.command()
async def opt_in(interaction: Interaction, dcs_username: str):
    server_data.log_user(dcs_username, True)
    await interaction.response.send_message(f"You've opted in to Digital Controllers events under the username `{dcs_username}`.")


@app_commands.command()
async def opt_out(interaction: Interaction, dcs_username: str):
    server_data.log_user(dcs_username, False)
    await interaction.response.send_message(f"You've opted out of Digital Controllers events under the username `{dcs_username}`.")


@app_commands.command()
async def ping(interaction: Interaction):
    latency = str(bot.latency)[:-13]
    await interaction.response.send_message(f"Pong! Ping is {latency}s.")


@app_commands.command()
@check_is_owner()
async def sync_command_tree(interaction: Interaction):
    await bot.tree.sync()
    await interaction.response.send_message("Tree synced.", ephemeral=True)


@app_commands.command()
@check_is_owner()
async def update_embed(interaction: Interaction):
    if bot.server_embed:
        await interaction.response.send_message("Embed update sequence has begun.", ephemeral=True)
        await bot.server_embed.update_embed()
    else:
        await interaction.response.send_message("Embed could not be found, creating new embed.", ephemeral=True)
        try:
            bot.server_embed = await tb_embeds.ServersEmbed.create(bot.get_channel(1099805791487266976))
            await interaction.followup.send("New embed created.", ephemeral=True)
        except AssertionError as err:
            await interaction.followup.send(f"Error trying to create embed.\nError text: {err}", ephemeral=True)


# =======BOT SETUP AND RUN=======


bot.tree.add_command(info)
bot.tree.add_command(metar)
bot.tree.add_command(opt_in)
bot.tree.add_command(opt_out)
bot.tree.add_command(ping)
bot.tree.add_command(sync_command_tree)
bot.tree.add_command(update_embed)
bot.run(TOKEN)
