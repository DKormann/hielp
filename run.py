from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json
from openai import OpenAI


settings = json.load(open(".env.json"))


client = OpenAI(api_key=settings["OPENAI_API_KEY"])


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

  if update.effective_user.id != settings['USER_ID']: return

  resp = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[{"role": "user", "content": update.message.text}],
  )
  await update.message.reply_text(resp.choices[0].message.content)


app = ApplicationBuilder().token(settings["TELEGRAM_TOKEN"]).build()
app.add_handler(CommandHandler("hello", hello))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

app.run_polling()
