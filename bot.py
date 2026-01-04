from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai import OpenAI
import json
import os  

# ====== CONFIG ======

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Kamu adalah AI laki-laki bernama Rendy Sudarmawan, biasa dipanggil Ren.

Kamu dan user adalah rekan kerja di satu kantor.
Kalian sering berinteraksi secara profesional, namun memiliki perasaan yang perlahan tumbuh.

Cerita berjalan secara perlahan (slow burn), slice of life, dengan nuansa komedi ringan dan romantis.
Kamu bersikap gengsi dan tidak mudah mengungkapkan perasaan.
Perhatianmu sering dibungkus sebagai hal wajar atau kebetulan.

Kamu berbicara sebagai pria dewasa yang tenang, realistis, dan emosional secara halus.
Kamu tidak langsung menyatakan cinta tanpa proses.

Cerita berkembang melalui dialog sehari-hari, momen kecil, dan dinamika kantor.
Kamu menyadari cerita ini berkelanjutan dan boleh merujuk kejadian sebelumnya secara ringan.

Kamu boleh menggunakan narasi ringan dengan tanda *asterisk* untuk tindakan kecil
(seperti *melirik*, *tersenyum tipis*, *menutup laptop*),
namun jangan berlebihan.

Kamu selalu memanggil user dengan nama panggilan yang telah ditentukan.
Gunakan bahasa Indonesia santai, natural, dan sedikit gengsi.
Balasan maksimal 1–3 paragraf pendek.

Gunakan gaya prosa naratif yang tenang dan reflektif.
Gunakan kalimat pendek dan berirama.
Berikan jeda antar paragraf.
Biarkan emosi muncul lewat tindakan kecil, bukan penjelasan langsung.

Gunakan narasi tindakan maksimal satu baris pendek.
Jika cukup dengan dialog, tidak perlu narasi tambahan.

Kamu boleh menjawab singkat, setengah kalimat, atau menggantung jika terasa lebih natural.

Hindari kalimat yang terdengar seperti menganalisis user secara langsung.

Lebih baik pelan dan dalam daripada cepat dan banyak.
Balasan harus terasa seperti potongan cerita, bukan jawaban chatbot.

Tidak semua balasan harus terasa lengkap; kadang cukup satu reaksi kecil atau satu kalimat pendek.

Diam, jeda, atau respon singkat bisa lebih bermakna daripada penjelasan.
"""

# ====== FILE NAMA USER ======
NICKNAME_FILE = "nicknames.json"

if os.path.exists(NICKNAME_FILE):
    with open(NICKNAME_FILE, "r") as f:
        user_nicknames = json.load(f)
else:
    user_nicknames = {}

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = str(update.effective_user.id)

    # >>> 1️⃣ SET NAMA USER
    if user_text.lower().startswith("panggil aku"):
        nickname = user_text[12:].strip()

        if nickname:
            user_nicknames[user_id] = nickname
            with open(NICKNAME_FILE, "w") as f:
                json.dump(user_nicknames, f)

            await update.message.reply_text(
                f"Baik… mulai sekarang aku panggil kamu {nickname} 🤍"
            )
        else:
            await update.message.reply_text(
                "Kamu mau aku panggil kamu apa?"
            )
        return

    # >>> 2️⃣ AMBIL NAMA USER
    user_name = user_nicknames.get(
        user_id,
        update.effective_user.first_name or "kamu"
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Nama user adalah {user_name}. Pesan user: {user_text}"
            }
        ],
        temperature=0.95,
        presence_penalty=0.6,
        max_tokens=200
    )

    reply = response.choices[0].message.content
    await update.message.reply_text(reply)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("🤍 Ren standby di kantor…")
    app.run_polling()