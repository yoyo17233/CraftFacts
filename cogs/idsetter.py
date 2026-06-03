import discord
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from discord.app_commands import AppCommandError, CheckFailure
from utils.perms import has_craft_perm, is_admin
from utils.data import guilds, save_guilds
from utils.logging import log

class IDSetterBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setfactchannel", description="Set the channel for craft facts")
    @has_craft_perm()
    async def setfactchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guilds[interaction.guild.id]["channel_id"] = channel.id
        save_guilds(guilds)
        await interaction.response.send_message(f"The channel <#{channel.id}> has been set for Facts!", ephemeral=True)

    @app_commands.command(name="setfactrole", description="Set the role to ping for craft facts")
    @has_craft_perm()
    async def setfactrole(self, interaction: discord.Interaction, role: discord.Role):
        guilds[interaction.guild.id]["ping_role_id"] = role.id
        save_guilds(guilds)
        await interaction.response.send_message(f"Role <@&{role.id}> will now be pinged!", ephemeral=True)

    @app_commands.command(name="setpermsrole", description="Set the role to be able to send craft fact commands")
    @is_admin()
    async def setpermsrole(self, interaction: discord.Interaction, role: discord.Role):
        guilds[interaction.guild.id]["perms_role_id"] = role.id
        save_guilds(guilds)
        await interaction.response.send_message(f"Role <@&{role.id}> now has fact permissions!", ephemeral=True)

    @app_commands.command(name="setfacttopic", description="Set the topic of the fun facts")
    @has_craft_perm()
    async def setfacttopic(self, interaction: discord.Interaction, topic: str):
        guilds[interaction.guild.id]["topic"] = topic
        save_guilds(guilds)
        await interaction.response.send_message(f"{topic} is now the topic of this servers daily facts!", ephemeral=True)

    @app_commands.command(name="settime", description="Set the time (EST) of the fun fact bot triggering in 24hour time")
    @has_craft_perm()
    async def settime(self, interaction: discord.Interaction, hour: str):
        guilds[interaction.guild.id]["hour"] = hour
        save_guilds(guilds)
        await interaction.response.send_message(f"Daily facts will now be sent at {hour}! (24hour time)", ephemeral=True)
        
    async def cog_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        log("handled inside IDSetter cog")
        if isinstance(error, CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send(str(error), ephemeral=True)
            else:
                await interaction.response.send_message(str(error), ephemeral=True)
        else:
            log(f"Unhandled error: {error}", "ERROR")

async def setup(bot: commands.Bot):
    await bot.add_cog(IDSetterBot(bot))