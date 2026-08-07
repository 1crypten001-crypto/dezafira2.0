import os
import threading
import telebot
from modules.database import get_db_blog_channels

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = None

def init_telegram_bot(on_chat_message_cb, on_produce_command_cb):
    global bot
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram Bot] TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID nao definidos. Bot inativo.")
        return

    try:
        bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
        print(f"[Telegram Bot] Bot inicializado para Chat ID: {TELEGRAM_CHAT_ID}")

        def is_owner(message):
            return str(message.chat.id) == str(TELEGRAM_CHAT_ID)

        @bot.message_handler(commands=['start', 'ajuda', 'help'])
        def send_welcome(message):
            if not is_owner(message):
                return
            welcome_text = (
                "🤖 *Olá, Jonatas! Eu sou o Hermes, seu assistente da Dezafira.*\n\n"
                "Comandos disponíveis:\n"
                "👉 `/artigos` - Lista artigos do blog\n"
                "👉 `/blogs` - Lista canais de blog\n"
                "👉 `/entregaveis` - Lista Mini Apps\n"
                "👉 `/escrever [tema]` - Gera artigo via IA\n"
                "👉 Qualquer texto - Conversa direto comigo!"
            )
            bot.reply_to(message, welcome_text, parse_mode="Markdown")

        @bot.message_handler(commands=['artigos', 'blogs'])
        def list_articles(message):
            if not is_owner(message):
                return
            try:
                from modules.database import get_db_blog_posts
                posts = get_db_blog_posts(limit=5)
                if not posts:
                    bot.reply_to(message, "ℹ️ Nenhum artigo encontrado.")
                    return
                response = "📝 *Artigos Recentes:*\n\n"
                for idx, p in enumerate(posts, 1):
                    status_emoji = "✅" if p['status'] == 'published' else "📝"
                    response += f"{idx}. {status_emoji} *{p['title'][:60]}*\n"
                    response += f"   Status: `{p['status']}` | {p.get('word_count', 0)} palavras\n\n"
                bot.reply_to(message, response, parse_mode="Markdown")
            except Exception as e:
                bot.reply_to(message, f"❌ Erro: {str(e)}")

        @bot.message_handler(commands=['entregaveis', 'mini-apps', 'pwas'])
        def list_deliverables(message):
            if not is_owner(message):
                return
            try:
                from modules.database import get_db_deliverable_apps
                apps = get_db_deliverable_apps()
                if not apps:
                    bot.reply_to(message, "ℹ️ Nenhum Mini App criado ainda.")
                    return
                response = "📱 *Mini Apps Disponiveis:*\n\n"
                for idx, a in enumerate(apps, 1):
                    response += f"{idx}. *{a['name']}* ({a['nicho']})\n"
                    response += f"   Slug: `{a['slug']}`\n\n"
                bot.reply_to(message, response, parse_mode="Markdown")
            except Exception as e:
                bot.reply_to(message, f"❌ Erro: {str(e)}")

        @bot.message_handler(commands=['escrever'])
        def write_article(message):
            if not is_owner(message):
                return
            parts = message.text.split(" ", 1)
            if len(parts) < 2:
                bot.reply_to(message, "⚠️ Especifique um tema. Exemplo: `/escrever O número 7 no Apocalipse`", parse_mode="Markdown")
                return
            theme = parts[1]
            bot.reply_to(message, f"🚀 *Gerando artigo sobre:* `{theme}`\nAguarde...", parse_mode="Markdown")
            threading.Thread(target=on_produce_command_cb, args=(theme,)).start()

        @bot.message_handler(func=lambda message: True)
        def handle_chat(message):
            if not is_owner(message):
                return
            user_text = message.text
            bot.send_chat_action(message.chat.id, 'typing')
            reply_text = on_chat_message_cb(user_text)
            bot.reply_to(message, reply_text)

        def run_polling():
            bot.infinity_polling()

        polling_thread = threading.Thread(target=run_polling, daemon=True)
        polling_thread.start()

        bot.send_message(TELEGRAM_CHAT_ID, "🟢 *Hermes conectado!* Digite `/ajuda` para ver os comandos.", parse_mode="Markdown")

    except Exception as e:
        print(f"[Telegram Bot] ❌ Falha ao iniciar bot: {str(e)}")

def send_telegram_notification(text: str):
    global bot
    if bot and TELEGRAM_CHAT_ID:
        try:
            bot.send_message(TELEGRAM_CHAT_ID, text, parse_mode="Markdown")
        except Exception as e:
            print(f"[Telegram Bot] Falha ao enviar notificação: {str(e)}")
