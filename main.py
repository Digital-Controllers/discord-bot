from datetime import datetime, timedelta
from discord import app_commands, Embed, File, Intents, Interaction
from discord.ext import commands, tasks
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from urllib.request import urlopen
import json
import os
import random
import server_data
import tb_embeds


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


# Creates and updates an embed every 120 seconds.
@tasks.loop(seconds=120)
async def update_server_embed():
    embed = Embed(title="DCS Server Information", description="Updated in real-time.",
                  color=0x3EBBE7)
    embed.set_author(name="Digital Controllers")
    embed.set_thumbnail(
        url="https://raw.githubusercontent.com/Digital-Controllers/website/main/docs/assets/logo.png")
    embed.set_footer(
        text="Want to add a new server to the embed? Propose it in #development or add a GitHub issue.")

    for server_name, server_info in (('GAW', server_data.gaw), ('PGAW', server_data.pgaw),
                                     ('LKEU', server_data.lkeu), ('LKNA', server_data.lkna)):
        response = ', '.join([value for key, value in server_info.items() if key not in {'players'}])
        embed.add_field(name=server_name, value=response, inline=False)

    try:
        channel = bot.get_channel(1108848019908071604)
        if bot.server_embed is None:
            bot.server_embed = await channel.send(embed=embed)
        else:
            await bot.server_embed.edit(embed=embed)
    except:
        print("Embed update failed.")


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


@bot.command()
@check_is_owner()
async def update_embed(ctx):
    await ctx.reply("Embed update sequence has begun.")
    await update_server_embed.start()


# =======APP COMMANDS=======


@app_commands.command()
async def ping(interaction: Interaction):
    latency = str(bot.latency)[:-13]
    await interaction.response.send_message(f"Pong! Ping is {latency}s.")


@app_commands.command()
async def opt_in(interaction: Interaction, dcs_username: str):
    server_data.log_user(dcs_username, True)
    await interaction.response.send_message(f"You've opted in to Digital Controllers events under the username {dcs_username}")


@app_commands.command()
async def opt_out(interaction: Interaction, dcs_username: str):
    server_data.log_user(dcs_username, False)
    await interaction.response.send_message(f"You've opted out of Digital Controllers events under the username {dcs_username}")


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
        details | str | Wanted statistics, defaults to all
    """
    server = name.value  # take the actual string value from the input Choice
    details = details.lower()

    try:
        stats = server_data.__getattr__(server)
    except AttributeError:
        interaction.response.send_message('Requested server could not be found')

    if details == 'all':
        await interaction.response.send_message(', '.join([value for key, value in stats.items() if key not in {'players'}]))
    if details == 'players':
        await interaction.response.send_message(embed=tb_embeds.PlayersEmbed(server, stats['players']))
    else:
        try:
            await interaction.response.send_message(stats[details])
        except KeyError:
            await interaction.response.send_message("Requested data isn't available for that server")


# =======BOT SETUP AND RUN=======


bot.tree.add_command(ping)
bot.tree.add_command(opt_in)
bot.tree.add_command(opt_out)
bot.tree.add_command(metar)
bot.tree.add_command(info)
bot.run(TOKEN)
