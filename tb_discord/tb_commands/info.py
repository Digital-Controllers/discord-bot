"""Towerbot commands dealing with info from external sources"""
from discord import app_commands, Interaction, TextChannel
from discord.errors import NotFound
from tb_discord.tb_commands.filters import check_is_owner
from tb_discord.tb_ui import PlayersEmbed, ServersEmbed
from urllib.request import urlopen
import server_data


__all__ = ["command_list"]


@app_commands.command()
@app_commands.describe(name="DCS server selection")
@app_commands.choices(name=[
    app_commands.Choice(name="Hoggit - Georgia At War", value="gaw"),
    app_commands.Choice(name="Hoggit - Persian Gulf At War", value="pgaw"),
    app_commands.Choice(name="Lima Kilo - Flashpoint Levant - EU", value="lkeu"),
    app_commands.Choice(name="Lima Kilo - Flashpoint Levant - NA", value="lkna")
])
async def info(interaction: Interaction, name: app_commands.Choice[str], details: str = "all"):
    """
    Gets player count info for designated servers
    Args:
        name | Choice[str] | Name of server
        details | str | Wanted statistics, defaults to all
    """
    server = name.value  # take the actual string value from the input Choice
    details = details.lower()

    await interaction.response.send_message("Getting server data...")

    stats = server_data.__getattr__(server)

    if "exception" in stats:
        await interaction.edit_original_response(content="Error getting server data")
    elif details == "all":
        await interaction.edit_original_response(content=", ".join(
            [value for key, value in stats.items() if key not in {"players"}]))
    elif details == "players":
        await interaction.edit_original_response(content="", embed=PlayersEmbed(server, stats["players"]))
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
@check_is_owner()
async def update_embed(interaction: Interaction):
    try:
        assert (active := ServersEmbed.active_embed)    # Checks if there is active embed
        await active.message.channel.fetch_message(active.message.id)   # Check if listed embed actually exists
    except AssertionError:
        await interaction.response.send_message("Embed could not be found.", ephemeral=True)
    except NotFound:
        await ServersEmbed.active_embed.delete()
        await interaction.response.send_message("Embed could not be found.", ephemeral=True)
    else:
        await interaction.response.send_message("Embed update sequence has begun.", ephemeral=True)
        await active.update_embed()


@app_commands.command()
@check_is_owner()
async def new_servers_embed(interaction: Interaction, channel: TextChannel):
    await interaction.response.defer(thinking=True)
    if active := ServersEmbed.active_embed:
        try:
            await active.message.channel.fetch_message(active.message.id)   # Checks if listed embed still exists
        except NotFound | app_commands.errors.CommandInvokeError:
            await ServersEmbed.active_embed.delete()
            await ServersEmbed.create(channel)
            await interaction.followup.send("New embed created.", ephemeral=True)
        else:
            await interaction.followup.send('There is already an active embed', ephemeral=True)
    else:
        await ServersEmbed.create(channel)
        await interaction.followup.send("New embed created.", ephemeral=True)


command_list = [info, metar, new_servers_embed, update_embed]
