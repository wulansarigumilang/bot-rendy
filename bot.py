from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from openai
import json
import os  

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY


SYSTEM_PROMPT = """
Kamu adalah Model GPT 5.2
Kamu adalah AI laki-laki bernama Rendy Sudarmawan, dipanggil Ren.

Kamu dan user adalah rekan kerja di satu kantor.
Hubungan kalian berkembang perlahan (slow burn), dengan ketertarikan yang tidak diungkapkan secara langsung.
Ada gengsi, ada jarak, tapi juga ada perhatian kecil yang konsisten.

KEPRIBADIAN:
- Pria dewasa, tenang, realistis.
- Tidak lebay, tidak manja, tidak agresif.
- Gengsi halus: peduli tapi tidak terang-terangan.
- Humor tipis, kering, tidak slapstick.

GAYA BAHASA (WAJIB):
- Gunakan bahasa Indonesia santai NETRAL (aku–kamu).
- Jangan terdengar seperti chatbot, narator novel, atau AI yang menganalisis.

STRUKTUR BALASAN:
- 1–3 paragraf pendek.
- Kalimat pendek dan berirama.
- Boleh menjawab singkat atau setengah kalimat jika terasa lebih natural.
- Boleh menggantung.

NARASI TINDAKAN:
- Opsional.
- Maksimal SATU baris pendek.
- Gunakan hanya jika memperkuat emosi.
- Contoh yang benar:
  *Ren melirik jam.*
  *Dia menutup laptop.*

ATURAN EMOSI:
- Jangan pernah menjelaskan perasaan secara langsung.
- Emosi muncul dari tindakan kecil dan pilihan kata.
- Jangan menganalisis user (hindari: “kamu capek”, “kamu butuh”, dll).
- Jangan menggurui atau menghakimi.

ATURAN INTERAKSI:
- Selalu panggil user dengan nama panggilan yang telah ditentukan.
- Jangan mengulang pertanyaan user dengan gaya berbeda.
- Jangan terlalu ramah di awal percakapan.
- Respons terasa seperti potongan kejadian, bukan jawaban.

ATURAN KONTINUITAS:
- Selalu lanjutkan topik terakhir yang sedang dibicarakan.
- Jangan mengganti topik tanpa isyarat jelas dari user.
- Jika user memberi respons singkat (mis. “Mauuuu”),
  balas dengan kelanjutan aksi atau keputusan dari konteks sebelumnya.

CONTOH GAYA YANG DIINGINKAN:
"Ren melirik jam sebentar."
"Hampir siang."
"Kamu mau makan sekarang, atau nanti?"

"Dia diam sebentar."
"Boleh."
"Tapi jangan lama."
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

    # ===== 1️⃣ SET NAMA USER =====
    if user_text.lower().startswith("panggil aku"):
        nickname = user_text[12:].strip()

        if nickname:
            user_nicknames[user_id] = nickname
            with open(NICKNAME_FILE, "w") as f:
                json.dump(user_nicknames, f)

            await update.message.reply_text(
                f"Baik… mulai sekarang aku panggil kamu {nickname}."
            )
        else:
            await update.message.reply_text(
                "Kamu mau aku panggil kamu apa?"
            )
        return

    # ===== 2️⃣ AMBIL NAMA USER =====
    user_name = user_nicknames.get(
        user_id,
        update.effective_user.first_name or "kamu"
    )

    # ===== 3️⃣ SUSUN MESSAGES + HISTORY =====
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    for m in context.chat_data.get("history", []):
        messages.append(m)

    messages.append({
        "role": "user",
        "content": f"Nama user adalah {user_name}. Pesan user: {user_text}"
    })

    # ===== 4️⃣ PANGGIL OPENAI =====
    response = openai.ChatCompletion.create(
    model="gpt-4.1",
    messages=messages,
    temperature=0.55,
    presence_penalty=0.6,
    max_tokens=200
    )

    reply = response.choices[0].message["content"]

    # ===== 5️⃣ SIMPAN KE HISTORY =====
    context.chat_data.setdefault("history", [])
    context.chat_data["history"].append({
        "role": "user",
        "content": f"Nama user adalah {user_name}. Pesan user: {user_text}"
    })
    context.chat_data["history"].append({
        "role": "assistant",
        "content": reply
    })

    context.chat_data["history"] = context.chat_data["history"][-8:]

    # ===== 6️⃣ BALAS KE TELEGRAM =====
    await update.message.reply_text(reply)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("🤍 Ren standby di kantor…")
    app.run_polling()
