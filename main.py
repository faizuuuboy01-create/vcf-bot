import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import vobject

TOKEN = os.environ.get("8150871986:AAFuCQYErxA2ov9OaNdsL2_P6m5Zy_P7OJs")  # Render pe environment variable se aayega

async def start(update: Update, context):
    await update.message.reply_text("Namaste! 🙏 Main VCF Bot hun. Mujhe kisi bhi contact forward karo, main VCF file bana dunga!")

async def handle_contact(update: Update, context):
    try:
        contact = update.message.contact
        vcard = vobject.vCard()
        vcard.add('fn').value = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
        vcard.add('tel').value = contact.phone_number
        
        filename = f"{contact.first_name or 'contact'}.vcf"
        with open(filename, 'w') as f:
            f.write(vcard.serialize())
        
        await update.message.reply_document(
            document=open(filename, 'rb'),
            caption="✅ Here's your VCF file!"
        )
    except Exception as e:
        await update.message.reply_text("❌ Kuch error aaya. Phir try karein.")

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.run_polling()