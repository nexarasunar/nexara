import logging
import re
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# AYARLAR — kendi değerlerinle değiştir
# ------------------------------------------------------------------
MASTER_BOT_TOKEN = "9217469115:AAFXQ-98p9xmFZNFso6sznDkqR1s1DOREYw"
PHOTO_PATH = "pp.jpg"  # VDS'de bu script ile AYNI klasörde olmalı
BOT_NAME = "Telegram"
BOT_DESCRIPTION = "Official Telegram Bot-Pavel Durov"
# ------------------------------------------------------------------

WAITING_TOKEN = 1
TOKEN_PATTERN = re.compile(r"^\d{6,10}:[A-Za-z0-9_-]{30,45}$")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Merhaba! Kapattırmak istediğin botun token'ını gönder.\n"
        "(BotFather'dan aldığın, '123456789:AA...' şeklindeki token)\n\n"
        "İptal etmek için /iptal yaz."
    )
    return WAITING_TOKEN


async def receive_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    token = update.message.text.strip()

    if not TOKEN_PATTERN.match(token):
        await update.message.reply_text(
            "Bu bir bot token'ına benzemiyor. Lütfen tekrar gönder veya /iptal yaz."
        )
        return WAITING_TOKEN

    await update.message.reply_text("Token kontrol ediliyor...")

    base_url = f"https://api.telegram.org/bot{token}"

    # 1) Token geçerli mi kontrol et
    try:
        me = requests.get(f"{base_url}/getMe", timeout=10).json()
    except requests.RequestException as e:
        await update.message.reply_text(f"Bağlantı hatası: {e}")
        return ConversationHandler.END

    if not me.get("ok"):
        await update.message.reply_text(f"Token geçersiz: {me.get('description')}")
        return ConversationHandler.END

    bot_username = me["result"].get("username", "bilinmiyor")
    await update.message.reply_text(f"Token doğrulandı: @{bot_username}")

    # 2) İsmi ayarla
    r = requests.post(f"{base_url}/setMyName", data={"name": BOT_NAME}, timeout=10).json()
    isim_sonuc = "✅ İsim ayarlandı" if r.get("ok") else f"❌ İsim ayarlanamadı: {r.get('description')}"

    # 3) Açıklamayı ayarla
    r = requests.post(
        f"{base_url}/setMyDescription", data={"description": BOT_DESCRIPTION}, timeout=10
    ).json()
    aciklama_sonuc = "✅ Açıklama ayarlandı" if r.get("ok") else f"❌ Açıklama ayarlanamadı: {r.get('description')}"

    # 4) Profil fotoğrafını ayarla (Bot API: setMyProfilePhoto)
    try:
        with open(PHOTO_PATH, "rb") as photo_file:
            files = {"photo": photo_file}
            data = {"photo": '{"type": "static", "photo": "attach://photo"}'}
            r = requests.post(
                f"{base_url}/setMyProfilePhoto", data=data, files=files, timeout=20
            ).json()
        foto_sonuc = "✅ Profil fotoğrafı ayarlandı" if r.get("ok") else f"❌ Fotoğraf ayarlanamadı: {r.get('description')}"
    except FileNotFoundError:
        foto_sonuc = f"❌ {PHOTO_PATH} bulunamadı. Dosyayı script ile aynı klasöre koy."

    await update.message.reply_text(
        "İşlem tamamlandı, Şimdi botun Profiline Gir, profilini büyüt Sağ Üst Köşedeki 3 noktaya tıkla bildir'e bas, taklite bas sonra tekrar taklite bas bunu 10kere yap ve bitti' :\n"
        f"{isim_sonuc}\n{aciklama_sonuc}\n{foto_sonuc}"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("İptal edildi.")
    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token(MASTER_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_token)],
        },
        fallbacks=[CommandHandler("iptal", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
