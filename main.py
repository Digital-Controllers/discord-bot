from datetime import datetime, timedelta
from discord import app_commands, File, Intents, Interaction
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from urllib.request import urlopen
import json
import os
import random
import sys

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

bot = commands.Bot(command_prefix='t?', intents=Intents.all())

print(f"Started at {str(datetime.utcnow())[:-16]}")

JETS = ["F16", "F18", "F15", "F35", "F22", "A10", "F14", "MIR2"]
HOLDING_POINTS = ["A", "B", "C", "D"]
AERODROMES = ["UG5X", "UG24", "UGKO", "UGKS", "URKA", "URKN", "URMM", "URSS"]
RUNWAYS = ["22", "04"]
DEPARTURES = ["GAM1D", "PAL1D", "ARN1D", "TIB1D", "SOR1D", "RUD1D", "AGI1D", "DIB1D", "TUN1D", "NAL1D"]
server_player_count_url_dict = {'gaw': 'https://status.hoggitworld.com/f67eecc6-4659-44fd-a4fd-8816c993ad0e',
                                'pgaw': 'https://status.hoggitworld.com/243bd8b1-3198-4c0b-817a-fadb40decf23',
                                'lkeu': 'https://levant.eu.limakilo.net/status/data',
                                'lkus': 'https://levant.na.limakilo.net/status/data'}


def check_is_owner():
    """
    Checks if author of a message is registered as owner in config.json
    Usage:
        @bot.command()
        @check_is_owner()
        async def command(...):
        will automatically say "Failed owner check." on failure
    Args:
        None
    Returns:
        True <or> AccessDeniedMessage | If owner is or is not in config
    """

    def predicate(ctx):
        if ctx.author.id not in cfg["OWNER_IDS"]:  # May not be coroutine-safe in the future, fine for now
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
    await bot.get_channel(1099805424934469652).send(f"Welcome to Digital Controllers, "
                                                    f"{member.name}!", file=File("strip.png"))
    os.remove("strip.png")


# =======BOT COMMANDS=======


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


# =======APP COMMANDS=======


@app_commands.command()
async def ping(interaction: Interaction):
    latency = str(bot.latency)[:-13]
    await interaction.response.send_message(f"Pong! Ping is {latency}s.")


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
                    f"https://beta.aviationweather.gov/cgi-bin/data/metar.php?ids={airport.upper()}&format=decoded") as x:
                data = x.read().decode("utf-8")
                if not data:
                    raise ValueError("Response was empty.")
                else:
                    await interaction.response.send_message(f"```{data}```")
        except:
            await interaction.response.send_message("Failed to fetch decoded METAR.")


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
        *sub_cats | tuple | List of wanted statistics, blank sends all
    """
    name = name.value  # take the actual string value from the input Choice
    details = details.lower()

    try:
        with urlopen(server_player_count_url_dict[name]) as pipe:
            response = pipe.read().decode('utf-8')
    except KeyError:  # If name isn't in server_player_count_url_dict then prevents execution
        await interaction.response.send_message('Specified DCS server could not be found')
        return
    except:  # PEP8 is screaming at me, but I don't know enough about urllib to figure out what error is thrown
        await interaction.response.send_message('Something went wrong trying to get the data. Try again, maybe?')
        return

    response_dict = json.loads(response)

    # Deal with different servers formatting json differently
    if name in {'gaw', 'pgaw'}:
        seconds_to_restart = timedelta(seconds=14400 - int(response_dict['data']['uptime']))
        response_strings = {'players': f"{int(response_dict['players']) - 1} player(s) online",  # Account for slmod?
                            'restart': f"Restart <t:{round((datetime.now() + seconds_to_restart).timestamp())}:R> ("
                                       f"may be inaccurate)",
                            'metar': f"METAR: {response_dict['data']['metar']}"}
    elif name in {'lkeu', 'lkus'}:
        seconds_to_restart = timedelta(seconds=int(response_dict['restartPeriod']) - int(response_dict['modelTime']))
        response_strings = {'players': f"{int(response_dict['players']['current']) - 1} player(s) online",
                            # Account for lk_admin
                            'restart': f"Restart <t:{round((datetime.now() + seconds_to_restart).timestamp())}:R>"}

    if details == 'all':
        await interaction.response.send_message(' | '.join(response_strings.values()))
    else:
        try:
            await interaction.response.send_message(response_strings[details])
        except KeyError:
            await interaction.response.send_message("Requested data isn't available for that server")


# =======BOT SETUP AND RUN=======


bot.tree.add_command(ping)
bot.tree.add_command(metar)
bot.tree.add_command(info)
bot.run(TOKEN)
