import os
import sys
import logging
from telebot import TeleBot, types

# إعداد البوت
TOKEN = '7329573835:AAFlixqkThrHE3las-J5c2GvKHVO_H_IFxA'
OWNER_ID = 6739658332
bot = TeleBot(TOKEN)

# إعداد اللوجر لتسجيل الأخطاء
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# مسار الملفات
UPLOAD_DIR = 'uploaded_bots'
os.makedirs(UPLOAD_DIR, exist_ok=True)

# قائمة الأدمن
ADMINS = [OWNER_ID]

# قاموس لتتبع العمليات النشطة
active_processes = {}

@bot.message_handler(commands=['start'])
def start_cmd(message):
    """رسالة الترحيب الرئيسية"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn1 = types.InlineKeyboardButton('📤 رفع ملف', callback_data='upload_file')
    btn2 = types.InlineKeyboardButton('⚡ سرعة البوت', callback_data='bot_speed')
    btn3 = types.InlineKeyboardButton('🎌 المطور', url='t.me/c8s8sx')
    btn4 = types.InlineKeyboardButton('🛑 إيقاف البوت', callback_data='stop_bot')
    
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_message(
        message.chat.id,
        f"مرحباً {message.from_user.first_name}! 👋\n\n"
        "أنا بوت تشغيل بوتات التليجرام بشكل آمن وسريع.\n"
        "يمكنك رفع ملفات Python أو ZIP وسأقوم بتشغيلها فوراً.\n\n"
        "🔸 للاستفسار: @c8s8sx",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'upload_file')
def ask_for_file(call):
    """طلب رفع الملف"""
    bot.send_message(call.message.chat.id, "📁 أرسل لي ملف البوت (py أو zip) الآن:")

@bot.callback_query_handler(func=lambda call: call.data == 'bot_speed')
def check_speed(call):
    """فحص سرعة البوت"""
    import time
    start = time.time()
    
    msg = bot.send_message(call.message.chat.id, "⏳ جاري فحص السرعة...")
    end = time.time()
    
    bot.edit_message_text(
        f"⚡ سرعة الاستجابة: {round((end - start) * 1000)} مللي ثانية",
        call.message.chat.id,
        msg.message_id
    )

@bot.callback_query_handler(func=lambda call: call.data == 'stop_bot')
def stop_user_bot(call):
    """إيقاف البوت الخاص بالمستخدم"""
    chat_id = call.message.chat.id
    if chat_id in active_processes:
        try:
            active_processes[chat_id].terminate()
            del active_processes[chat_id]
            bot.answer_callback_query(call.id, "✅ تم إيقاف البوت بنجاح")
        except:
            bot.answer_callback_query(call.id, "❌ فشل في إيقاف البوت")
    else:
        bot.answer_callback_query(call.id, "⚠️ لا يوجد بوت نشط لإيقافه")

@bot.message_handler(content_types=['document'])
def handle_bot_file(message):
    """معالجة ملفات البوتات المرسلة"""
    try:
        # الحصول على معلومات الملف
        file_info = bot.get_file(message.document.file_id)
        file_name = message.document.file_name
        
        # التأكد من أن الملف بايثون أو zip
        if not (file_name.endswith('.py') or file_name.endswith('.zip')):
            bot.reply_to(message, "❌我只接受Python或ZIP文件")
            return
        
        # تحميل الملف
        downloaded_file = bot.download_file(file_info.file_path)
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        # حفظ الملف
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        
        # إذا كان ملف zip، فك الضغط
        if file_name.endswith('.zip'):
            import zipfile
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(os.path.join(UPLOAD_DIR, file_name[:-4]))
            
            # البحث عن الملف الرئيسي
            main_file = None
            extracted_dir = os.path.join(UPLOAD_DIR, file_name[:-4])
            
            for f in os.listdir(extracted_dir):
                if f in ['bot.py', 'main.py', 'start.py']:
                    main_file = os.path.join(extracted_dir, f)
                    break
            
            if not main_file:
                bot.reply_to(message, "❌ لم يتم العثور على ملف رئيسي (bot.py/main.py/start.py)")
                return
            
            file_path = main_file
        
        # تشغيل البوت
        bot.reply_to(message, "🚀 جاري تشغيل البوت...")
        
        # استخدام nohup للحفاظ على العملية مستمرة
        import subprocess
        process = subprocess.Popen([
            'nohup', 'python3', file_path, '&'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # تتبع العملية
        active_processes[message.chat.id] = process
        bot.reply_to(message, "✅ تم تشغيل البوت بنجاح!")
        
    except Exception as e:
        logger.error(f"Error handling file: {e}")
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

# أوامر الأدمن
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """لوحة تحكم الأدمن"""
    if message.from_user.id not in ADMINS:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn1 = types.InlineKeyboardButton('📊 الإحصائيات', callback_data='admin_stats')
    btn2 = types.InlineKeyboardButton('🛑 إيقاف الكل', callback_data='admin_stopall')
    btn3 = types.InlineKeyboardButton('🔄 إعادة التشغيل', callback_data='admin_restart')
    
    markup.add(btn1, btn2, btn3)
    
    bot.send_message(
        message.chat.id,
        "🔧 **لوحة تحكم الأدمن**\n\n"
        "إختر الإجراء المطلوب:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_actions(call):
    """معالجة إجراءات الأدمن"""
    if call.from_user.id not in ADMINS:
        return
    
    if call.data == 'admin_stats':
        stats = f"👥 المستخدمين: {len(active_processes)}\n"
        stats += f"🖥 العمليات النشطة: {len(active_processes)}"
        bot.answer_callback_query(call.id, stats)
    
    elif call.data == 'admin_stopall':
        for pid, process in active_processes.items():
            try:
                process.terminate()
            except:
                pass
        active_processes.clear()
        bot.answer_callback_query(call.id, "✅ تم إيقاف جميع العمليات")
    
    elif call.data == 'admin_restart':
        bot.answer_callback_query(call.id, "🔄 جاري إعادة التشغيل...")
        os.execv(sys.executable, ['python'] + sys.argv)

# تشغيل البوت
if __name__ == '__main__':
    logger.info("Starting bot...")
    print("✅ البوت يعمل الآن!")
    bot.infinity_polling()