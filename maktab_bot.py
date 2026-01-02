import logging
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
from datetime import datetime

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ma'lumotlar bazasi (oddiy JSON)
class MaktabDB:
    def __init__(self):
        self.data = {
            'users': {
                # Demo foydalanuvchi - o'zgartiring
                '123456789': {  # ← Bu yerga o'z Telegram ID'ingizni qo'ying
                    'role': 'parent',
                    'name': 'Demo Ota-ona',
                    'children': ['student_1'],
                    'registered': True
                }
            },
            'students': {
                'student_1': {
                    'name': 'Ali Valiyev',
                    'class': '7-A',
                    'grades': [
                        {'subject': 'Matematika', 'grade': 5, 'date': '2025-01-15'},
                        {'subject': 'Ona tili', 'grade': 4, 'date': '2025-01-14'},
                        {'subject': 'Ingliz tili', 'grade': 5, 'date': '2025-01-13'}
                    ],
                    'attendance': [
                        {'date': '2025-01-15', 'status': 'present'},
                        {'date': '2025-01-14', 'status': 'present'},
                        {'date': '2025-01-13', 'status': 'absent'}
                    ]
                }
            },
            'schedule': {
                '7-A': {
                    'Dushanba': ['Matematika', 'Ona tili', 'Ingliz tili', 'Jismoniy'],
                    'Seshanba': ['Fizika', 'Tarix', 'Adabiyot', 'Informatika'],
                    'Chorshanba': ['Matematika', 'Kimyo', 'Biologiya', 'San\'at'],
                    'Payshanba': ['Ona tili', 'Ingliz tili', 'Geografiya', 'Musiqa'],
                    'Juma': ['Matematika', 'Informatika', 'Jismoniy', 'Tarbiya']
                }
            },
            'homework': {
                '7-A': [
                    {'subject': 'Matematika', 'task': '№125, 126', 'deadline': '2025-01-17'},
                    {'subject': 'Ona tili', 'task': 'Insho yozish', 'deadline': '2025-01-18'}
                ]
            },
            'announcements': [
                {'title': 'Ota-onalar yig\'ilishi', 'text': '20-yanvar soat 16:00', 'date': '2025-01-10'}
            ]
        }
    
    def get_user(self, telegram_id):
        return self.data['users'].get(str(telegram_id))
    
    def get_student_grades(self, student_id):
        student = self.data['students'].get(student_id)
        return student['grades'] if student else []
    
    def get_student_attendance(self, student_id):
        student = self.data['students'].get(student_id)
        return student['attendance'] if student else []
    
    def get_schedule(self, class_name, day):
        return self.data['schedule'].get(class_name, {}).get(day, [])
    
    def get_homework(self, class_name):
        return self.data['homework'].get(class_name, [])
    
    def get_announcements(self):
        return self.data['announcements']

db = MaktabDB()

# Keyboards
def get_main_keyboard(role):
    if role == 'parent':
        return ReplyKeyboardMarkup([
            [KeyboardButton("📊 Baholar"), KeyboardButton("📅 Davomat")],
            [KeyboardButton("📚 Uy vazifalar"), KeyboardButton("📖 Dars jadvali")],
            [KeyboardButton("📢 E'lonlar"), KeyboardButton("ℹ️ Yordam")]
        ], resize_keyboard=True)
    return ReplyKeyboardMarkup([[KeyboardButton("ℹ️ Yordam")]], resize_keyboard=True)

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = str(user.id)
    user_data = db.get_user(telegram_id)
    
    if user_data:
        keyboard = get_main_keyboard(user_data['role'])
        await update.message.reply_text(
            f"🎓 Assalomu alaykum, {user_data['name']}!\n\n"
            f"Maktab botiga xush kelibsiz.\n"
            f"Kerakli bo'limni tanlang:",
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            f"👋 Assalomu alaykum, {user.first_name}!\n\n"
            f"🎓 Maktab botiga xush kelibsiz!\n\n"
            f"Sizning Telegram ID: `{telegram_id}`\n\n"
            f"Administrator siz uchun ruxsat berishi kerak.",
            parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    telegram_id = str(update.effective_user.id)
    user_data = db.get_user(telegram_id)
    
    if not user_data:
        await update.message.reply_text("❌ Ruxsat yo'q. Admin bilan bog'laning.")
        return
    
    if text == "📊 Baholar":
        student_id = user_data['children'][0]
        grades = db.get_student_grades(student_id)
        
        msg = "📊 *BAHOLAR*\n\n"
        for g in reversed(grades):
            msg += f"📚 {g['subject']}: *{g['grade']}* ({g['date']})\n"
        
        avg = sum(g['grade'] for g in grades) / len(grades)
        msg += f"\n📈 O'rtacha: *{avg:.1f}*"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    elif text == "📅 Davomat":
        student_id = user_data['children'][0]
        attendance = db.get_student_attendance(student_id)
        
        msg = "📅 *DAVOMAT*\n\n"
        present = 0
        for a in attendance:
            emoji = "✅" if a['status'] == 'present' else "❌"
            msg += f"{emoji} {a['date']}\n"
            if a['status'] == 'present':
                present += 1
        
        pct = (present / len(attendance)) * 100
        msg += f"\n📊 Davomat: *{pct:.0f}%*"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    elif text == "📚 Uy vazifalar":
        student = db.data['students'][user_data['children'][0]]
        homework = db.get_homework(student['class'])
        
        msg = "📚 *UY VAZIFALAR*\n\n"
        for hw in homework:
            msg += f"📖 {hw['subject']}\n   {hw['task']}\n   Muddat: {hw['deadline']}\n\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    elif text == "📖 Dars jadvali":
        student = db.data['students'][user_data['children'][0]]
        days = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma']
        today = days[datetime.now().weekday()] if datetime.now().weekday() < 5 else 'Dushanba'
        
        schedule = db.get_schedule(student['class'], today)
        
        msg = f"📖 *DARS JADVALI*\n*Bugun: {today}*\n\n"
        for i, subject in enumerate(schedule, 1):
            msg += f"{i}. {subject}\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    elif text == "📢 E'lonlar":
        announcements = db.get_announcements()
        
        msg = "📢 *E'LONLAR*\n\n"
        for ann in announcements:
            msg += f"📌 *{ann['title']}*\n   {ann['text']}\n   {ann['date']}\n\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    elif text == "ℹ️ Yordam":
        msg = """
ℹ️ *YORDAM*

📊 Baholar - Farzand baholarini ko'rish
📅 Davomat - Davomat ma'lumotlari
📚 Uy vazifalar - Uy vazifalar ro'yxati
📖 Dars jadvali - Bugungi darslar
📢 E'lonlar - Maktab e'lonlari

Savollar uchun: @admin
        """
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    else:
        await update.message.reply_text("❓ Tushunmadim. Menyudan tanlang.")

def main():
    # TOKEN - Render.com environment variable'dan oladi
    TOKEN = os.environ.get('BOT_TOKEN')
    
    if not TOKEN:
        logger.error("❌ BOT_TOKEN topilmadi!")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🤖 Bot ishga tushdi!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
