import discord, os
from discord.ext import commands
from utils.utilities import dm_user, userToDm_id
from utils.data import init_data

VERBOSE = True

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.guilds = True  
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await dm_user(bot, userToDm_id, "on_ready called")

    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
        
        await bot.change_presence(
            activity=discord.Game(f"Daily Facts"),
            status=discord.Status.online
        )

    except Exception as e:
        print(f"Error syncing commands: {e}")
    
    init_data(bot)

async def load_cogs():
    await bot.load_extension("cogs.craftfacts")
    await bot.load_extension("cogs.idsetter")

@bot.event
async def setup_hook():
    await dm_user(bot, userToDm_id, "setup_hook called")
    await load_cogs()

bot.run(TOKEN)