import discord
from discord.app_commands import CheckFailure
from discord import app_commands
from utils.data import guilds
from utils.utilities import superusers

VERBOSE = True

def has_craft_perm():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            raise CheckFailure("This command can only be used in a server.")
        perms_role_id = guilds[interaction.guild.id]["perms_role_id"]

        if not perms_role_id:
            raise CheckFailure("Permissions role not set.")

        if any(role.id == perms_role_id for role in interaction.user.roles):
            return True

        raise CheckFailure("You don't have permission to use this command.")
    return app_commands.check(predicate)

def is_admin():
    async def predicate(interaction) -> bool:
        if interaction.permissions.administrator:
            return True
        raise CheckFailure("You must be an Administrator to use this command.")
    return app_commands.check(predicate)

def is_superuser():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id in superusers:
            return True
        else:
            raise CheckFailure("You don't have permission to use this command.")
    return app_commands.check(predicate)

def check_is_admin(interaction: discord.Interaction) -> bool:
    if interaction.permissions.administrator:
        return True
    return False
    
def check_is_superuser(interaction: discord.Interaction) -> bool:
    if interaction.user.id in superusers:
        return True
    return False
    
def is_gemini_allowed():
    async def predicate(interaction) -> bool:
        if interaction.guild is None:
            raise CheckFailure("This command can only be used in a server.")
        if guilds[interaction.guild.id]["geminiperms"]:
            return True
        raise CheckFailure("Gemini commands are disabled in this server.")
    return app_commands.check(predicate)

def is_channel_set():
    async def predicate(interaction) -> bool:
        if interaction.guild is None:
            raise CheckFailure("This command can only be used in a server.")
        if guilds[interaction.guild.id]["channel_id"]:
            return True
        raise CheckFailure("Channel is not set for this server")
    return app_commands.check(predicate)

def check_is_channel_set(guild_id) -> bool:
    return guilds[guild_id]["channel_id"]
