import json, os
from dotenv import load_dotenv

load_dotenv()
CONFIG_FILE = os.getenv("CONFIG_FILE")

DEFAULT_GUILD_CONFIG = {
    "channel_id": 0,
    "ping_role_id": 0,
    "perms_role_id": 0,
    "hour": 10,
    "geminiperms": False,
    "topic":"Generic (No Topic)",
    "previousfacts":[]
}

def load_guilds():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({}, f, indent=4)
    with open(CONFIG_FILE, "r") as f:
        raw = json.load(f)
        return {int(k): v for k, v in raw.items()} # Casting string keys back into ints

def save_guilds(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def init_data(bot):
    updated = False
    for guild in bot.guilds:
        print("checking guild", guild.id)
        if guild.id not in guilds:
            guilds[guild.id] = DEFAULT_GUILD_CONFIG
            updated = True
    if updated:
        save_guilds(guilds)

guilds = load_guilds()