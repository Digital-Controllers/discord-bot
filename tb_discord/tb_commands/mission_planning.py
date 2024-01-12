"""Towerbot commands dealing with mission and event planning"""
from discord import app_commands, Interaction, ScheduledEvent
from tb_discord.tb_commands.filters import check_is_staff
import server_data


__all__ = ["command_list"]


@app_commands.command()
async def opt_in(interaction: Interaction, dcs_username: str):
    if len(dcs_username) <= 25:
        server_data.log_user(dcs_username, True)
        await interaction.response.send_message(f"You've opted in to Digital Controllers events under the username `{dcs_username}`.")
    else:
        await interaction.response.send_message("DCS Usernames have a length limit of 25 characters, please try again.")


@app_commands.command()
async def opt_out(interaction: Interaction, dcs_username: str):
    if len(dcs_username) <= 25:
        server_data.log_user(dcs_username, False)
        await interaction.response.send_message(f"You've opted out of Digital Controllers events under the username `{dcs_username}`.")
    else:
        await interaction.response.send_message("DCS Usernames have a length limit of 25 characters, please try again.")


@app_commands.command()
@check_is_staff()
async def ping_event(inter: Interaction, event_name: str):
    await inter.response.defer(thinking=True, ephemeral=True)
    events = await inter.guild.fetch_scheduled_events()
    filter(lambda event: event.name.lower() == event_name.lower(), events)
    if len(events) > 1:
        await inter.followup.send("There is more than one event with that name", ephemeral=True)
    elif len(events) == 0:
        await inter.followup.send("There are no events with that name", ephemeral=True)
    else:
        users = []
        async for user in events[0].users():
            users.append(user)

        await inter.followup.send("<@" + "><@".join([str(user.id) for user in users]) + ">")


command_list = [opt_in, opt_out, ping_event]
