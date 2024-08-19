import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json
from openai import OpenAI
import os

settings = json.load(open(".env.json"))
client = OpenAI(api_key=settings["OPENAI_API_KEY"])

os.makedirs("data/users", exist_ok=True)

class User:
  def __init__(self, user: telegram.User, hist=None):
    if os.path.exists(f"data/users/{user.id}"):
      hist = json.load(open(f"data/users/{user.id}/messages.json"))
    else:
      hist = []
      json.dump(hist, open(f"data/users/{user.id}/messages.json", "w"))
      json.dump({"first_name": user.first_name, "last_name": user.last_name, "username": user.username, "id": user.id}, open(f"data/users/{user.id}/info.json", "w"))
    self.name = user.first_name or user.username
    self.id = user.id
    self.hist = hist

  def save(self):
    with open(f"data/users/{self.id}/info.json", "w") as f: json.dump({"name": self.name, "id": self.id}, f)
    with open(f"data/users/{self.id}/messages.json", "w") as f: json.dump(self.hist, f)

  def send_message(self, message):
    self.hist.append({"role": "user", "content": message})
    self.save()
    resp = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=self.hist[-10:]
    ).choices[0].message.content
    self.hist.append({"role": "bot", "content": resp})
    self.save()
    return resp

users = {}
def get_user(user: User):
  if user.id not in users: users[user.id] = User(user)
  return users[user.id]


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

  user = get_user(update.message.from_user)
  await update.message.reply_text(user.send_message(update.message.text))

app = ApplicationBuilder().token(settings["TELEGRAM_TOKEN"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

app.run_polling()
