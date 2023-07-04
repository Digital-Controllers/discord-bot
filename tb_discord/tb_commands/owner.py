"""Towerbot commands dealing with bot management"""
from configs import configs
from discord import app_commands, Interaction, TextChannel
from discord.errors import NotFound
from tb_discord.tb_ui import ServersEmbed
from tb_discord import bot


__all__ = ['command_list']


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
        if interaction.user.id not in configs.owner_ids:  # May not be coroutine-safe in the future, fine for now
            return False
        return True

    return app_commands.check(predicate)


@app_commands.command()
@check_is_owner()
async def new_servers_embed(interaction: Interaction, channel: TextChannel):
    await interaction.response.defer(thinking=True)
    if active := ServersEmbed.active_embed:
        try:
            await active.message.channel.fetch_message(active.message.id)   # Checks if listed embed still exists
        except NotFound:
            await ServersEmbed.active_embed.delete()
            await ServersEmbed.create(channel)
            await interaction.followup.send("New embed created.", ephemeral=True)
        else:
            await interaction.followup.send('There is already an active embed', ephemeral=True)
    else:
        await ServersEmbed.create(channel)
        await interaction.followup.send("New embed created.", ephemeral=True)


@app_commands.command()
@check_is_owner()
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


command_list = [new_servers_embed, ping, sync_command_tree, update_embed]
