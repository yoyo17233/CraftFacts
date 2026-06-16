import discord, asyncio
from discord.ext import commands, tasks
from discord import app_commands
from discord.app_commands import AppCommandError, CheckFailure
from utils.utilities import get_facts, wait_until_hour, ask_gemini, send_facts, send_fact, wait_until_generating_time
from utils.perms import has_craft_perm, is_channel_set, is_gemini_allowed
from utils.logging import log

MAX_LEN = 2000
CHUNK_LIMIT = 3

class CraftFacts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.hourly_task.start()
        self.daily_task.start()

    def cog_unload(self):
        self.hourly_task.cancel()
        self.daily_task.cancel()

    @tasks.loop(hours=1)
    async def hourly_task(self):
        await self.bot.wait_until_ready()
        await send_facts(self)

    @hourly_task.before_loop
    async def before_hourly_task(self):
        await wait_until_hour()

    @tasks.loop(hours=24)
    async def daily_task(self):
        await self.bot.wait_until_ready()
        await get_facts()

    @daily_task.before_loop
    async def before_daily_task(self):
        await wait_until_generating_time()
    '''
    @app_commands.command(name="craftfact", description="Gets a random craft fact")
    @has_craft_perm()
    @is_channel_set()
    async def craftfact(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"craftfact on the way!", ephemeral=True)
        await send_fact(self, interaction.guild.id)
    '''
    @app_commands.command(name="gemini", description="Ask Gemini anything!")
    @has_craft_perm()
    @is_gemini_allowed()
    async def gemini(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        status_msg = await interaction.followup.send("Asking Gemini...", wait=True)
        loop = asyncio.get_running_loop()
        try: 
            response = await loop.run_in_executor(None, ask_gemini, query)
        except Exception as e:
            if "503" in str(e):
                await status_msg.edit(content="Gemini is currently overloaded. Please try again later.")
                return
            elif "429" in str(e):
                await status_msg.edit(content="Google API rate limit exceeded. Please wait before asking Gemini again.")
                return
            else:
                await status_msg.edit(content=f"Unknown error occurred while asking Gemini: {e}")
                return

        chunks = []
        text = response
        while text:
            if len(text) <= MAX_LEN:
                chunks.append(text)
                break
            cutoff = text.rfind('.', 0, MAX_LEN)
            if cutoff == -1:
                cutoff = MAX_LEN
            chunks.append(text[:cutoff + 1].strip())
            text = text[cutoff + 1:].strip()

        truncated = len(chunks) > CHUNK_LIMIT
        if truncated:
            chunks = chunks[:CHUNK_LIMIT]

        await status_msg.edit(content=chunks[0])
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk)
        if truncated:
            await interaction.followup.send("Response too long, trimmed.")
        
    @app_commands.command(name="help", description="Show all CraftFacts commands")
    @has_craft_perm()
    async def help(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "```\n"
            "User Commands\n"
            "  /craftfact       - Send an immediate CraftFact to this channel\n"
            "  /gemini          - Ask Gemini AI anything\n"
            "    query          -> Your question or prompt\n"
            "  /changetopic     - Change the topic for this server's daily facts\n"
            "    topic          -> New fact topic\n"
            "  /changetime      - Change the time the daily fact is sent (24h EST)\n"
            "    hour           -> Hour to send daily facts (24h format)\n"
            "  /help            - Show this message\n"
            "\n"
            "Admin Command\n"
            "  /setup           - Initial bot setup for this server\n"
            "    fact_role      -> Role to ping for daily facts\n"
            "    perms_role     -> Role required to use commands\n"
            "    topic          -> Topic for fact generation\n"
            "    hour           -> Hour to send daily facts (24h EST)\n"
            "```",
            ephemeral=True
        )

    async def cog_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        if isinstance(error, CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send(str(error), ephemeral=True)
            else:
                await interaction.response.send_message(str(error), ephemeral=True)
        else:
            log(f"Unhandled error handled in CraftFacts cog: {error}", "ERROR")

async def setup(bot: commands.Bot):
    await bot.add_cog(CraftFacts(bot))
    log("Starting CraftFacts")