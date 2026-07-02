import os, asyncio
from datetime import datetime, timedelta
from google import genai
from dotenv import load_dotenv
from utils.data import guilds, save_guilds
from utils.logging import log

load_dotenv()
GEMINIKEY = os.getenv("GEMINI_API_KEY")
if not GEMINIKEY:
    raise RuntimeError("GEMINI_API_KEY is not set")
DMS = os.getenv("DMS", "False").lower() in ("true", "1", "yes")
SUPERUSERS = os.getenv("SUPERUSERS", "")
superusers = [int(x) for x in SUPERUSERS.split(",") if x.strip()]
userToDm_id = superusers[0] if superusers else None
client = genai.Client(api_key=GEMINIKEY)
MAX_FACT_RETRIES = 3

FACT_DELIMITER = "---"
introprompt = "You are a fact expert writing in the style of Snapple facts. Generate a true, interesting, and surprising fact in a short, friendly tone. Make sure it is accurate, easy to understand, and sounds like it could be loged under a bottle cap. Use clear and concise wording, no more than 1–2 sentences. Begin the fact directly, like: ‘Did you know...’ or ‘Honey never spoils...’ Avoid common facts, urban legends, or anything misleading or unverified. Double-check that it is scientifically or historically correct."
categorization = "Summarize the fact in as few words as possible, for example, ‘flamingo group name’ for a flamboyance of flamingos, or ‘temperature of lightning’. If the fact’s topic is not ‘Generic’, give the subtopic, and provide more detail without including the greater topic name, still only using a couple of words. If the topic is ‘Generic’, a simple topic name is sufficient."
    
def ask_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    if response.text is None:
        raise ValueError("Gemini returned no text")
    return response.text

async def dm_user(bot, user_id, message):
    if(not DMS or user_id is None):
        log(f"DMs are disabled or no superuser set, skipping DM: {message}", "WARN")
        return
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        log(f"DM sent to {user.global_name}")
    except Exception as e:
        log(f"Failed to DM user: {e}", "ERROR")

async def get_facts():
    log("Starting daily fact generation...")
    for guild in guilds:
        await get_fact(guild)

async def get_fact(guild_id):
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

    attempts = 0
    while attempts < MAX_FACT_RETRIES:
        try:
            attempts += 1
            raw = await loop.run_in_executor(None, ask_gemini, prompt)
            parts = raw.split(FACT_DELIMITER, 1)
            fact = parts[0].strip()
            subtopic = parts[1].strip() if len(parts) > 1 else "General"
            attempts = MAX_FACT_RETRIES  # Exit loop after successful generation
        except Exception as e:
            log(f"Gemini failed to generate fact for guild {guild_id} on attempt {attempts}: {e}", "ERROR")
            if attempts >= MAX_FACT_RETRIES:
                return None
            await asyncio.sleep(60)

    guilds[guild_id]["stored_fact"] = fact

    if len(previous_facts) >= 30:
        previous_facts.pop()
    previous_facts.insert(0, subtopic)

    save_guilds(guilds)
    log(f"Fact retrieved for guild {guild_id}: {fact} (Subtopic: {subtopic})")
    return fact

async def send_facts(self):
    now_hour = datetime.now().hour
    for guild_id, guild_data in guilds.items():
        if guild_data.get("hour") == now_hour:
            await send_fact(self, guild_id)

async def send_fact(self, guild_id):
    if not guilds[guild_id]["channel_id"] or not guilds[guild_id]["ping_role_id"]:
        log(f"Guild {guild_id} attempted to send a craftfact but is missing channel or ping role configuration", "ERROR")
        return
    fact = guilds[guild_id].get("stored_fact")
    if not fact:
        fact = await get_fact(guild_id)
    if not fact:
        log(f"Fact generation failed for guild {guild_id}", "ERROR")
        return
    channel = self.bot.get_channel(guilds[guild_id]["channel_id"])
    await channel.send(f"<@&{guilds[guild_id]['ping_role_id']}> Incoming CraftFact! (With topic *{guilds[guild_id]['topic']}*)\n\n**{fact}**")
    log("Single CraftFact sent to guild " + str(guild_id))
    guilds[guild_id]["stored_fact"] = None
    save_guilds(guilds)
    
async def wait_until_hour():
    now = datetime.now()
    target = (now + timedelta(hours=1)).replace(minute=0, second=4, microsecond=0)      #Live
    #target = datetime.now() + timedelta(seconds=10)                                     #Testing
    await asyncio.sleep((target - now).total_seconds())

async def wait_until_generating_time():
    now = datetime.now()
    target_time_str = os.getenv("FACT_GENERATION_TIME", "5:19:36")
    target_hour, target_minute, target_second = map(int, target_time_str.split(":"))
    target = now.replace(hour=target_hour, minute=target_minute, second=target_second, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    log(f"Generating facts at {target.strftime('%H:%M:%S')} EST")
    await asyncio.sleep((target - now).total_seconds())