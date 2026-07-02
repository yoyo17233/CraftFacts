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

    @app_commands.command(name="setup", description="Initial setup: set fact channel, roles, topic, and time")
    @is_admin()
    async def setup(
        self,
        interaction: discord.Interaction,
        fact_role: discord.Role,
        perms_role: discord.Role,
        topic: str,
        hour: str,
    ):
        if interaction.guild is None or interaction.channel is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        guild = guilds[interaction.guild.id]
        guild["channel_id"] = interaction.channel.id
        guild["ping_role_id"] = fact_role.id
        guild["perms_role_id"] = perms_role.id
        guild["topic"] = topic
        guild["hour"] = hour
        save_guilds(guilds)
        await interaction.response.send_message(
            f"Setup complete!\n"
            f"- Fact channel: <#{interaction.channel.id}>\n"
            f"- Ping role: <@&{fact_role.id}>\n"
            f"- Permissions role: <@&{perms_role.id}>\n"
            f"- Topic: {topic}\n"
            f"- Time: {hour} (24h EST)",
            ephemeral=True,
        )

    @app_commands.command(name="changetopic", description="Change the topic of the daily facts")
    @has_craft_perm()
    async def changetopic(self, interaction: discord.Interaction, topic: str):
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        guilds[interaction.guild.id]["topic"] = topic
        save_guilds(guilds)
        await interaction.response.send_message(f"{topic} is now the topic of this server's daily facts!", ephemeral=True)

    @app_commands.command(name="changetime", description="Change the time (EST) the daily fact is sent (24h format)")
    @has_craft_perm()
    async def changetime(self, interaction: discord.Interaction, hour: str):
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        guilds[interaction.guild.id]["hour"] = hour
        save_guilds(guilds)
        await interaction.response.send_message(f"Daily facts will now be sent at {hour}! (24h time)", ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        if isinstance(error, CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send(str(error), ephemeral=True)
            else:
                await interaction.response.send_message(str(error), ephemeral=True)
        else:
            log(f"Unhandled error handled in IDSetter cog: {error}", "ERROR")

async def setup(bot: commands.Bot):
    await bot.add_cog(IDSetterBot(bot))
