import os, asyncio
from datetime import datetime, timedelta
from google import genai
from dotenv import load_dotenv
from utils.data import guilds, save_guilds

load_dotenv()
GEMINIKEY = os.getenv("GEMINI_API_KEY")
DMS = os.getenv("DMS", "False").lower() in ("true", "1", "yes")
SUPERUSERS = os.getenv("SUPERUSERS")
superusers = [int(x) for x in SUPERUSERS.split(",") if x.strip()]
userToDm_id = superusers[0]
client = genai.Client(api_key=GEMINIKEY)

introprompt = "You are a fact expert writing in the style of Snapple facts. Generate a true, interesting, and surprising fact in a short, friendly tone. Make sure it is accurate, easy to understand, and sounds like it could be printed under a bottle cap. Use clear and concise wording, no more than 1–2 sentences. Begin the fact directly, like: 'Did you know...' or 'Honey never spoils...' Avoid common facts, urban legends, or anything misleading or unverified. Double-check that it is scientifically or historically correct."
categorization = "Summarize the fact in as few words as possible, for example, 'flamingo group name' for a flamboyance of flamingos, or 'temperature of lightning'. If the fact’s topic is not 'Generic', give the subtopic, and provide more detail without including the greater topic name, still only using a couple of words. If the topic is 'Generic', a simple topic name is sufficient."
    
def ask_gemini(prompt: str) -> str:
    print(f"Sending prompt to Gemini")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    print("Received response from Gemini: ", response.text)
    return response.text

async def dm_user(bot, user_id, message):
    if(not DMS):
       print(f"User DMs disabled, skipping...")
       return
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        print(f"DM sent to {user.global_name}")
    except Exception as e:
        print(f"Failed to DM user: {e}")

async def get_fact(guild_id):
    previous_facts = guilds[guild_id]["previousfacts"]
    topic = guilds[guild_id]["topic"]

    loop = asyncio.get_running_loop()
    fact = await loop.run_in_executor(None, ask_gemini, f"{introprompt}\n\nDo not make it about the following facts:{previous_facts} The topic of the fact should be: {topic}, but you can be broad")
    subtopic = await loop.run_in_executor(None, ask_gemini, f"{categorization} The fact to categorize is: {fact}")

    if len(previous_facts) >= 30:
        previous_facts.pop() 
    previous_facts.insert(0, subtopic)
    save_guilds(guilds)

    return fact

async def send_facts(self):
    now_hour = datetime.now().hour
    print(f"the hour is {now_hour}")
    for guild_id, guild_data in guilds.items():
        print("checking guild to see if it has channel + roles set")
        if(not guild_data.get("channel_id") or not guild_data.get("ping_role_id")):
            return
        print(f"checking guildid {guild_id} if it has {guild_data.get("hour")} as time of {now_hour}")
        if guild_data.get("hour") == now_hour:
            print("getting fact...")
            fact = await get_fact(guild_id)
            print(f"Fact is {fact}, getting channel...")
            channel = self.bot.get_channel(guilds[guild_id]["channel_id"])
            print("got channel, sending...")
            await channel.send(f"<@&{guild_data.get("ping_role_id")}> Incoming CraftFact! (With topic *{guild_data.get("topic")}*)\n\n**{fact}**")
            print("sent")

async def send_fact(self, guild_id):
    print("checking guild to see if it has channel + roles set")
    if(not guilds[guild_id]["channel_id"] or not guilds[guild_id]["ping_role_id"]):
        return
    print("getting fact...")
    fact = await get_fact(guild_id)
    print(f"Fact is {fact}, getting channel...")
    channel = self.bot.get_channel(guilds[guild_id]["channel_id"])
    print("got channel, sending...")
    await channel.send(f"<@&{guilds[guild_id]["ping_role_id"]}> Incoming CraftFact! (With topic *{guilds[guild_id]["topic"]}*)\n\n**{fact}**")
    print("sent")
    
async def wait_until_hour():
    now = datetime.now()
    target = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)\
    #target = datetime.now() + timedelta(seconds=10)
    await asyncio.sleep((target - now).total_seconds())