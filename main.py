import discord
import requests
import os
import json

# --- SETTINGS ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "mixtral-8x7b-32768"
MAX_MEMORY = 10
MEMORY_FILE = "memory.json"
# ----------------

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# Load previous memory
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {}

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def chat_with_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": messages
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user.mentioned_in(message) or message.content.startswith("!ai"):
        channel_id = str(message.channel.id)

        # Init memory
        if channel_id not in memory:
            memory[channel_id] = []

        user_input = message.content.replace("!ai", "").strip()
        memory[channel_id].append({"role": "user", "content": user_input})
        memory[channel_id] = memory[channel_id][-MAX_MEMORY:]

        try:
            reply = chat_with_groq(memory[channel_id])
            memory[channel_id].append({"role": "assistant", "content": reply})
            save_memory()
            await message.reply(reply)
        except Exception as e:
            await message.reply(f"⚠️ Error: {e}")

client.run(DISCORD_TOKEN)
