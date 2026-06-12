import os
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8682290553:AAHrttDETB9wNfQScVF4NLMLo1UULqtvHuI")
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
- Responder: відповідає клієнтам у WhatsApp
- Scout: шукає нових партнерів
- Analyst: аналізує дані і готує звіти

Відповідай українською, коротко і по суті.
"""

conversation_history = []

def ask_hunter(question: str) -> str:
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        system=HUNTER_SYSTEM,
        messages=[{"role": "user", "content": question}]
    )
    return response.content[0].text

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

def main():
    print("Boss Agent запущено!")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
