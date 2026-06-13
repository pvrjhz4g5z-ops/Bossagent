import os
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

RESPONDER_TOKEN = os.environ.get("RESPONDER_TOKEN", "8904031380:AAGyr66k7xSdMWt_wRKtERXYMbm2EFxJwWQ")
ANTHROPIC_KEY  = os.environ.get("ANTHROPIC_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

RESPONDER_SYSTEM = """
Ти — консультант магазину аксесуарів для iPhone та WHOOP 5.0
(чохли, картхолдери, ремінці).
Відповідай клієнтам ввічливо, коротко, українською.
Допомагай вибрати товар, відповідай на питання про ціни,
доставку, наявність. Якщо не знаєш точної ціни — скажи що
уточниш у менеджера.
"""

conversations = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text

    if chat_id not in conversations:
        conversations[chat_id] = []

    conversations[chat_id].append({"role": "user", "content": user_text})
    await update.message.reply_chat_action("typing")

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        system=RESPONDER_SYSTEM,
        messages=conversations[chat_id]
    )
    reply = response.content[0].text
    conversations[chat_id].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)

def main():
    print("Responder запущено!")
    app = ApplicationBuilder().token(RESPONDER_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
