"""Towerbot commands dealing with mission planning things"""
from discord import app_commands, Interaction
import server_data


__all__ = ['command_list']


@app_commands.command()
async def opt_in(interaction: Interaction, dcs_username: str):
    server_data.log_user(dcs_username, True)
    await interaction.response.send_message(f"You've opted in to Digital Controllers events under the username `{dcs_username}`.")


@app_commands.command()
async def opt_out(interaction: Interaction, dcs_username: str):
    server_data.log_user(dcs_username, False)
    await interaction.response.send_message(f"You've opted out of Digital Controllers events under the username `{dcs_username}`.")


command_list = [opt_in, opt_out]
