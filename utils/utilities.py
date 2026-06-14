import os, asyncio, time
from datetime import date, datetime, timedelta
from google import genai
from dotenv import load_dotenv
from utils.data import guilds, save_guilds
from utils.logging import log

load_dotenv()
GEMINIKEY = os.getenv("GEMINI_API_KEY")
DMS = os.getenv("DMS", "False").lower() in ("true", "1", "yes")
SUPERUSERS = os.getenv("SUPERUSERS")
superusers = [int(x) for x in SUPERUSERS.split(",") if x.strip()]
userToDm_id = superusers[0]
client = genai.Client(api_key=GEMINIKEY)

FACT_DELIMITER = "---"
introprompt = "You are a fact expert writing in the style of Snapple facts. Generate a true, interesting, and surprising fact in a short, friendly tone. Make sure it is accurate, easy to understand, and sounds like it could be loged under a bottle cap. Use clear and concise wording, no more than 1–2 sentences. Begin the fact directly, like: ‘Did you know...’ or ‘Honey never spoils...’ Avoid common facts, urban legends, or anything misleading or unverified. Double-check that it is scientifically or historically correct."
categorization = "Summarize the fact in as few words as possible, for example, ‘flamingo group name’ for a flamboyance of flamingos, or ‘temperature of lightning’. If the fact’s topic is not ‘Generic’, give the subtopic, and provide more detail without including the greater topic name, still only using a couple of words. If the topic is ‘Generic’, a simple topic name is sufficient."
    
def ask_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

async def dm_user(bot, user_id, message):
    if(not DMS): 
       return
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        log(f"DM sent to {user.global_name}")
    except Exception as e:
        log(f"Failed to DM user: {e}", "ERROR")

async def get_fact(bot, guild_id):
    previous_facts = guilds[guild_id]["previousfacts"]
    topic = guilds[guild_id]["topic"]
    loop = asyncio.get_running_loop()

    prompt = (
        f"{introprompt}\n\n"
        f"Do not make it about the following facts: {previous_facts}\n"
        f"The topic of the fact should be: {topic}, but you can be broad.\n\n"
        f"After the fact, write '{FACT_DELIMITER}' on its own line, then write a short subtopic label. "
        f"Subtopic instructions: {categorization}"
    )

    try:
        raw = await loop.run_in_executor(None, ask_gemini, prompt)
        parts = raw.split(FACT_DELIMITER, 1)
        fact = parts[0].strip()
        subtopic = parts[1].strip() if len(parts) > 1 else "General"
    except Exception as e:
        log(f"Gemini failed to generate fact for guild {guild_id}: {e}", "ERROR")
        return None

    if len(previous_facts) >= 30:
        previous_facts.pop()
    previous_facts.insert(0, subtopic)
    save_guilds(guilds)
    log(f"Fact retrieved, subtopic: {subtopic}")

    return fact

async def send_facts(self):
    now_hour = datetime.now().hour
    for guild_id, guild_data in guilds.items():
        if not guild_data.get("channel_id") or not guild_data.get("ping_role_id"):
            continue
        if guild_data.get("hour") == now_hour:
            fact = await get_fact(self.bot, guild_id)
            if fact is None:
                log(f"Skipping guild {guild_id} — fact generation failed", "ERROR")
                continue
            channel = self.bot.get_channel(guilds[guild_id]["channel_id"])
            await channel.send(f"<@&{guild_data.get('ping_role_id')}> Incoming CraftFact! (With topic *{guild_data.get('topic')}*)\n\n**{fact}**")
            log("Daily fact sent to guild " + str(guild_id))

async def send_fact(self, guild_id):
    if not guilds[guild_id]["channel_id"] or not guilds[guild_id]["ping_role_id"]:
        return
    fact = await get_fact(self.bot, guild_id)
    if fact is None:
        log(f"Fact generation failed for guild {guild_id}", "ERROR")
        return
    channel = self.bot.get_channel(guilds[guild_id]["channel_id"])
    await channel.send(f"<@&{guilds[guild_id]['ping_role_id']}> Incoming CraftFact! (With topic *{guilds[guild_id]['topic']}*)\n\n**{fact}**")
    log("Single CraftFact sent to guild " + str(guild_id))
    
async def wait_until_hour():
    now = datetime.now()
    target = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)      #Live
    #target = datetime.now() + timedelta(seconds=10)                                     #Testing
    await asyncio.sleep((target - now).total_seconds())