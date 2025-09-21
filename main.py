import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import vobject
import sqlite3

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")  # Your Telegram User ID

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS approved_users
                 (user_id INTEGER PRIMARY KEY, username TEXT, date_approved TEXT)''')
    conn.commit()
    conn.close()

def is_approved(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM approved_users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def add_approved_user(user_id, username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO approved_users (user_id, username, date_approved) VALUES (?, ?, datetime('now'))",
              (user_id, username))
    conn.commit()
    conn.close()

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if is_approved(user_id):
        await update.message.reply_text("✅ Welcome back! Send me a contact to convert to VCF.")
    else:
        await update.message.reply_text("⏳ Your access is pending approval. Please wait...")
        # Notify admin
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🚨 New user requested access:\nUser ID: {user_id}\nUsername: @{username}\n\nApprove with: /approve_{user_id}"
        )

# Admin approval command
async def approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if str(user_id) != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /approve <user_id>")
        return
    
    target_user_id = int(context.args[0])
    add_approved_user(target_user_id, "unknown")
    
    await update.message.reply_text(f"✅ User {target_user_id} approved!")
    # Notify user
    await context.bot.send_message(
        chat_id=target_user_id,
        text="🎉 Your access has been approved! You can now use the bot forever!"
    )

# Contact handler
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_approved(user_id):
        await update.message.reply_text("❌ You are not approved yet. Please wait for approval.")
        return
    
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
        await update.message.reply_text("❌ Error creating VCF file.")

if __name__ == "__main__":
    init_db()
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve_command))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    
    app.run_polling()