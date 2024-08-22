import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
import os, threading, asyncio, json
from encrypt import encrypt
import gzip

settings = json.load(open(".env.json"))
client = OpenAI(api_key=settings["OPENAI_API_KEY"])

os.makedirs("data/users", exist_ok=True)
app = ApplicationBuilder().token(settings["TELEGRAM_TOKEN"]).build()

sysprompt = 'You are a helpful management assistant that helps people accomplish there personal goals. However you concise and careful not to talk to much expecially about banal things. You offer help only when asked.'

class User:
  def __init__(self, id:int, name:str, hist=None):
    self.name = name
    self.id = id
    if os.path.exists(f"data/users/{id}"):
      # self.hist = json.load(open(f"data/users/{id}/messages.json"))
      data = open(f"data/users/{id}/messages", "rb").read()
      try:
        data = encrypt.decrypt(data)
        data = gzip.decompress(data)
        self.hist = json.loads(data.decode())
      except:
        print("error: invalid master password")
        exit()
    else:
      self.hist = []
      os.makedirs(f"data/users/{id}", exist_ok=True)
      self.save()

  def save(self):
    with open(f"data/users/{self.id}/info.json", "w") as f: json.dump({"name": self.name, "id": self.id}, f)
    hist_data:bytes = json.dumps(self.hist)
    hist_data = gzip.compress(hist_data.encode(), 1)
    hist_data = encrypt.encrypt(hist_data)
    with open(f"data/users/{self.id}/messages", "wb") as f: f.write(hist_data)

  def get_bot_response(self):
    return client.chat.completions.create(
      model="gpt-4o-mini",
      messages= [{'role':'system', 'content':sysprompt}] + self.hist[-10:]
    ).choices[0].message.content

  async def send_assistant_to_user(self, message:str):
    self.hist.append({"role": "assistant", "content": message})
    self.save()
    await app.bot.send_message(self.id, message)

  async def send_user_to_assistant(self, message:str):
    self.hist.append({"role": "user", "content": message})
    self.save()
    await self.send_assistant_to_user(self.get_bot_response())
  
  async def send_system_to_assistant(self, message:str):
    self.hist.append({"role": "system", "content": message})
    self.save()
    await self.send_assistant_to_user(self.get_bot_response())

async def wakey(context):
  for user in users.values():
    await user.send_system_to_assistant("It is 9 am, please wake the user up. Ask him about how he feels first and after he responded, ask what he is going to accomplish today.")

import datetime
app.job_queue.run_repeating(wakey, 60*60*24, datetime.datetime.now().replace(hour=9, minute=0))

users:dict[int, User] = {}

for user in os.listdir("data/users"):
  user = json.load(open(f"data/users/{user}/info.json"))
  users[user["id"]] = User(user["id"], user["name"])

  users[user["id"]].save()

def get_user(user: telegram.User):
  if user.id not in users: users[user.id] = User(user.id, user.first_name or user.username)
  return users[user.id]

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user = get_user(update.effective_user)
  await app.bot.send_chat_action(update.message.chat_id, "typing")
  await user.send_user_to_assistant(update.message.text)

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
app.run_polling()