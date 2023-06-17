"""Collect all data from tb_command groups into a single interface for bot usage"""
import tb_discord.tb_commands.info
import tb_discord.tb_commands.mission_planning
import tb_discord.tb_commands.owner
import tb_discord.tb_commands.roles


__all__ = ['command_list']


command_list = info.command_list + mission_planning.command_list + owner.command_list + roles.command_list
