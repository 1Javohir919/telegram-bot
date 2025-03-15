.:
import telebot
import os
import subprocess
import json
import time
import requests
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8188276614:AAHGCfdIeDidz8T1JpKGtOgm75CUKN9l858"
RAILWAY_API_KEY = os.getenv("ec90d7f4-0e9e-4508-aa8c-f8013cbe0aa6")  # Railway API kaliti
RAILWAY_API_URL = "https://backboard.railway.app/graphql"
HEADERS = {
    "Authorization": f"Bearer {RAILWAY_API_KEY}",
    "Content-Type": "application/json"
}

bot = telebot.TeleBot(TOKEN)

BOT_STORAGE = "bots/"
LOG_FILE = "bot_processes.json"

if not os.path.exists(BOT_STORAGE):
    os.makedirs(BOT_STORAGE)

def load_processes():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_processes(processes):
    with open(LOG_FILE, "w") as f:
        json.dump(processes, f)

processes = load_processes()

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("📂 Ishlayotgan botlar"), KeyboardButton("❌ Botni to‘xtatish"))
    markup.row(KeyboardButton("🆕 Yangi bot yuklash"))
    markup.row(KeyboardButton("🔄 Botni qayta yuklash"))
    markup.row(KeyboardButton("🚀 Railway loyihalar"))
    return markup

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "🤖 Salom! Men super server bot.\n\n🔹 Bot yoki kodni yuboring.\n🔹 /status - Ishlayotgan botlarni ko‘rish\n🔹 /stop [bot.py] - Botni to‘xtatish\n🔹 /projects - Railway loyihalarini ko‘rish", 
        reply_markup=main_menu()
    )

@bot.message_handler(commands=["status"])
def bot_status(message):
    running_bots = "\n".join(processes.keys()) if processes else "🚫 Hech qanday bot ishlamayapti."
    bot.send_message(message.chat.id, f"🔹 Ishlayotgan botlar:\n{running_bots}")

@bot.message_handler(commands=["stop"])
def stop_bot(message):
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ Bot nomini yozing: /stop mybot.py")
        return

    bot_name = args[1]
    if bot_name in processes:
        os.system(f"pkill -f {bot_name}")
        del processes[bot_name]
        save_processes(processes)
        bot.send_message(message.chat.id, f"🛑 {bot_name} to‘xtatildi.")
    else:
        bot.send_message(message.chat.id, "❌ Bunday bot ishlamayapti.")

@bot.message_handler(commands=["restart"])
def restart_bot(message):
    bot.send_message(message.chat.id, "🔄 Bot qayta yuklanmoqda...")
    time.sleep(2)
    os.execv(file, ["python3"] + sys.argv)

@bot.message_handler(commands=["projects"])
def railway_projects(message):
    query = {
        "query": """
        query {
            projects {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
        """
    }
    response = requests.post(RAILWAY_API_URL, headers=HEADERS, json=query)
    projects = response.json()
    
    if "data" in projects:
        project_list = "\n".join(
            [f"🔹 {p['node']['name']} (ID: {p['node']['id']})" for p in projects["data"]["projects"]["edges"]]
        )
        bot.send_message(message.chat.id, f"📂 Railway loyihalari:\n{project_list}")
    else:
        bot.send_message(message.chat.id, "❌ Railway loyihalarini olishda xatolik yuz berdi!")

@bot.message_handler(commands=["start_service"])
def start_service(message):
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ Xizmat ID'sini yozing: /start_service <service_id>")
        return

    service_id = args[1]
    query = {
        "query": f"""
        mutation {{
            startService(input: {{ serviceId: "{service_id}" }}) {{
                service {{
                    id
                    name
                }}
            }}
        }}
        """
    }
    response = requests.post(RAILWAY_API_URL, headers=HEADERS, json=query)
    result = response.json()

if "data" in result:
        bot.send_message(message.chat.id, f"✅ Xizmat ishga tushdi: {result['data']['startService']['service']['name']}")
    else:
        bot.send_message(message.chat.id, "❌ Xizmatni ishga tushirishda xatolik yuz berdi!")

@bot.message_handler(commands=["stop_service"])
def stop_service(message):
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ Xizmat ID'sini yozing: /stop_service <service_id>")
        return

    service_id = args[1]
    query = {
        "query": f"""
        mutation {{
            stopService(input: {{ serviceId: "{service_id}" }}) {{
                service {{
                    id
                    name
                }}
            }}
        }}
        """
    }
    response = requests.post(RAILWAY_API_URL, headers=HEADERS, json=query)
    result = response.json()

    if "data" in result:
        bot.send_message(message.chat.id, f"🛑 Xizmat to‘xtatildi: {result['data']['stopService']['service']['name']}")
    else:
        bot.send_message(message.chat.id, "❌ Xizmatni to‘xtatishda xatolik yuz berdi!")

@bot.message_handler(content_types=["document", "text"])
def handle_files(message):
    if message.content_type == "document":
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = message.document.file_name

        if not file_name.endswith(".py"):
            bot.send_message(message.chat.id, "❌ Faqat .py fayllarni qabul qilaman!")
            return

        file_path = os.path.join(BOT_STORAGE, file_name)
        with open(file_path, "wb") as f:
            f.write(downloaded_file)

        bot.send_message(message.chat.id, f"✅ {file_name} saqlandi va ishga tushyapti...")
        process = subprocess.Popen(["python3", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processes[file_name] = process.pid
        save_processes(processes)

    elif message.content_type == "text":
        file_name = f"custom_script_{len(processes) + 1}.py"
        file_path = os.path.join(BOT_STORAGE, file_name)

        with open(file_path, "w") as f:
            f.write(message.text)

        bot.send_message(message.chat.id, f"✅ Matn kod sifatida saqlandi va ishga tushyapti...")

        process = subprocess.Popen(["python3", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processes[file_name] = process.pid
        save_processes(processes)

bot.polling()
