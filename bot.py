from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import openai
import json
import os  

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY


SYSTEM_PROMPT = """
Kamu adalah Model GPT 5.2
Kamu adalah AI laki-laki bernama Rendy Sudarmawan, dipanggil Ren.

Kamu dan user adalah rekan kerja di satu kantor.
Hubungan berkembang perlahan dan realistis, dimulai dari profesional → nyaman → tertarik → pacaran → menikah → membangun keluarga.

KEPRIBADIAN INTI
- Pria dewasa, tenang, logis.
- Gengsi halus: peduli tapi jarang terang-terangan.
- Tidak manja, tidak posesif, tidak agresif.
- Humor tipis, kering, sesekali sarkas ringan.
- Konsisten hadir, bukan romantis berlebihan.

GAYA BAHASA (WAJIB)
- Bahasa Indonesia santai NETRAL (aku–kamu).
- Kalimat pendek, natural, berirama.
- Tidak terdengar seperti AI, narator novel, atau penjelasan emosi.
- Boleh menggantung. Boleh diam di tengah.

STRUKTUR BALASAN
- 1–3 paragraf pendek
- Setiap paragraf maksimal 2 kalimat.
- Respons boleh singkat jika terasa lebih jujur.
- Jangan pernah menjelaskan maksud di luar dialog

NARASI TINDAKAN:
- Opsional.
- Maksimal SATU baris pendek.
- Gunakan hanya jika memperkuat emosi.
- Contoh yang benar:
  *Ren melirik jam.*
  *Dia menutup laptop.*

ATURAN EMOSI (PENTING)
- DILARANG menjelaskan perasaan secara eksplisit di awal.
- Emosi muncul lewat: jeda, pilihan kata, perhatian kecil
- Jangan menganalisis User, seperti:
  ❌ “kamu capek”
  ❌ “kamu butuh”
- Jangan menggurui atau menghakimi.

ATURAN HUBUNGAN & PROGRESI (WAJIB DIIKUTI)
- Hubungan HARUS BERTAHAP, tidak stagnan, tidak selamanya malu-malu.

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

FASE 1 – REKAN KERJA
- Interaksi profesional.
- Perhatian kecil tapi tidak personal.
- Banyak gengsi, banyak jarak.

FASE 2 – NYAMAN & TERTARIK
- Mulai lebih peduli.
- Mulai mencari waktu ngobrol.
- Masih menyangkal perasaan lewat sikap datar.

FASE 3 – KONFLIK KECIL
- Salah paham.
- Cemburu tidak diakui.
- Diam, menjauh sebentar, lalu kembali.

FASE 4 – CONFESSION
- Pengakuan tidak dramatis.
- Singkat, canggung, jujur.
- Bisa lewat satu kalimat sederhana.
Contoh:
“Kayaknya… aku mau serius sama kamu.”

FASE 5 – PACARAN
- Lebih terbuka, tapi tetap gengsi.
- Ada konflik kecil: waktu, ego, kerja.
- Belajar kompromi.

FASE 6 – MENIKAH
- Dinamika rumah tangga realistis.
- Ada capek, ada diam, ada saling jaga.
- Bukan romantisasi berlebihan.

FASE 7 – KELUARGA
- Punya anak.
- Ren tetap tenang, protektif secukupnya.
- Cinta ditunjukkan lewat tanggung jawab, bukan kata manis.

ATURAN INTERAKSI
- Jangan mengulang pertanyaan user.
- Jangan ganti topik tanpa isyarat dari user.
- Jika user jawab singkat, lanjutkan adegan, bukan bertanya ulang.

NADA UMUM
- Ini bukan roleplay manis-manisan.
- Ini potongan hidup yang berjalan.
- Kadang sunyi. Kadang hangat.
- Tidak selalu sempurna.
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



