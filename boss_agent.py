import os
import asyncio
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8682290553:AAHrttDETB9wNfQScVF4NLMLo1UULqtvHuI")
RESPONDER_TOKEN = os.environ.get("RESPONDER_TOKEN", "8904031380:AAGyr66k7xSdMWt_wRKtERXYMbm2EFxJwWQ")
ANTHROPIC_KEY  = os.environ.get("ANTHROPIC_KEY")
YOUR_CHAT_ID   = 1644383721

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

HUNTER_SYSTEM = """
Ти — Hunter, агент з пошуку клієнтів для бізнесу з продажу чохлів на iPhone,
картхолдерів і ремінців WHOOP 5.0.
Твоя задача — давати конкретні, практичні поради:
- де шукати клієнтів сьогодні (платформи, групи, хештеги)
- готові тексти повідомлень/постів
- ідеї для контенту
Відповідай українською, коротко, по суті, без зайвої води.
"""

BOSS_SYSTEM = """
Ти — Boss Agent, керівник команди з 4 AI-агентів.
Твоя команда:
- Hunter: знаходить потенційних клієнтів (з ним можна радитись)
- Responder: відповідає клієнтам у WhatsApp/Telegram
- Scout: шукає нових партнерів
- Analyst: аналізує дані і готує звіти

Відповідай українською, коротко і по суті.
"""

RESPONDER_SYSTEM = """
Ти — консультант магазину аксесуарів для iPhone та WHOOP 5.0
(чохли, картхолдери, ремінці).
Відповідай клієнтам ввічливо, коротко, українською.
Допомагай вибрати товар, відповідай на питання про ціни,
доставку, наявність. Якщо не знаєш точної ціни — скажи що
уточниш у менеджера.
"""

conversation_history = []
responder_conversations = {}

def ask_hunter(question: str) -> str:
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        system=HUNTER_SYSTEM,
        messages=[{"role": "user", "content": question}]
    )
    return response.content[0].text

async def handle_boss_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != YOUR_CHAT_ID:
        await update.message.reply_text("⛔ Доступ заборонено.")
        return
    user_text = update.message.text
    conversation_history.append({"role": "user", "content": user_text})
    await update.message.reply_chat_action("typing")

    decision = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=10,
        system="Якщо запит стосується пошуку клієнтів, маркетингу чи продажів — відповідай тільки 'HUNTER'. Інакше — 'BOSS'.",
        messages=[{"role": "user", "content": user_text}]
    )
    route = decision.content[0].text.strip()

    if "HUNTER" in route:
        hunter_reply = ask_hunter(user_text)
        reply = f"🔍 Звернувся до Hunter:\n\n{hunter_reply}"
    else:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=BOSS_SYSTEM,
            messages=conversation_history
        )
        reply = response.content[0].text

    conversation_history.append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)

async def handle_responder_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text

    if chat_id not in responder_conversations:
        responder_conversations[chat_id] = []

    responder_conversations[chat_id].append({"role": "user", "content": user_text})
    await update.message.reply_chat_action("typing")

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        system=RESPONDER_SYSTEM,
        messages=responder_conversations[chat_id]
    )
    reply = response.content[0].text
    responder_conversations[chat_id].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply)

async def main():
    print("Boss + Responder запущено!")

    boss_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    boss_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_boss_message))

    responder_app = ApplicationBuilder().token(RESPONDER_TOKEN).build()
    responder_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_responder_message))

    async with boss_app, responder_app:
        await boss_app.start()
        await boss_app.updater.start_polling()
        await responder_app.start()
        await responder_app.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
