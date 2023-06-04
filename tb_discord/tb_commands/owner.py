"""Towerbot commands dealing with bot management"""
from configs import configs
from discord import app_commands, Interaction
from tb_discord.tb_embeds.private import ServersEmbed
from tb_discord import bot
import logging


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
            bot.server_embed = await ServersEmbed.create(bot.get_channel(configs.dc_embed_channel_id))
            await interaction.followup.send("New embed created.", ephemeral=True)
        except AssertionError as err:
            await interaction.followup.send(f"Error trying to create embed.\nError text: {err}", ephemeral=True)
            logging.error('Bot failed to create embed; error text: %s', str(err))


command_list = [sync_command_tree, update_embed]
