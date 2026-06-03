import discord, asyncio
from discord.ext import commands, tasks
from discord import app_commands
from discord.app_commands import AppCommandError, CheckFailure
from utils.utilities import wait_until_hour, ask_gemini, send_facts, send_fact
from utils.perms import has_craft_perm, is_channel_set, is_gemini_allowed
from utils.logging import log

class CraftFacts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.hourly_task.start()

    def cog_unload(self):
        self.hourly_task.cancel()

    @tasks.loop(hours=1)
    async def hourly_task(self):
        await self.bot.wait_until_ready()
        log("Hourly task triggered!")
        await send_facts(self)

    @hourly_task.before_loop
    async def before_hourly_task(self):
        await wait_until_hour()

    @app_commands.command(name="craftfact", description="Gets a random craft fact")
    @has_craft_perm()
    @is_channel_set()
    async def craftfact(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"craftfact on the way!", ephemeral=True)
        await send_fact(self, interaction.guild.id)

    @app_commands.command(name="gemini", description="Ask Gemini anything!")
    @has_craft_perm()
    @is_gemini_allowed()
    async def gemini(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        status_msg = await interaction.followup.send("Asking Gemini...", wait=True)
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, ask_gemini, query)

        chunks = []
        max_len = 2000
        text = response

        while len(text) > max_len:
            cutoff = text.rfind('.', 0, max_len)
            if cutoff == -1:
                cutoff = max_len

            chunks.append(text[:cutoff+1].strip())
            text = text[cutoff+1:].strip()

        if len(chunks) < 3 and text:
            chunks.append(text)
        elif len(text) > 0:
            chunks.append("Message too long, message trimmed")

        await status_msg.edit(content=chunks[0])

        for chunk in chunks[1:]:
            await interaction.followup.send(chunk)
        
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
    await bot.add_cog(CraftFacts(bot))
    log("Starting CraftFacts")