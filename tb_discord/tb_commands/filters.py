"""Permission filters for Towerbot"""
from discord import app_commands
from discord import Interaction
from configs import configs


__all__ = ["check_is_owner", "check_is_staff"]


def check_is_staff():
    """
    Checks if author of a message has a DC staff or administrator role
    Usage:
        @bot.command()
        @check_is_owner()
        async def command(...):
        Commands with this check should not appear to any non-admin
    Returns:
        True or False | If owner is or is not in config
    """
    def predicate(interaction: Interaction):
        for role in configs.staff_role_ids:
            if role in map(lambda x: x.id, interaction.user.roles):
                return True
        return False

    return app_commands.check(predicate)


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
