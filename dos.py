# هذا السكريبت يعالج البيانات من الإنترنت بشكل آمن وفي الذاكرة فقط
# لتجنب انتهاك قواعد الأمان المتعلقة بالوصول إلى نظام الملفات.

import telebot
import requests
import re
from urllib.parse import urlparse

# ==============================================================
#                 إعدادات الاتصال والتوكن
# ==============================================================
API_TOKEN = "7802577795:AAFpLwlEimYtFdRGPEiZD-tbfX2l2c30MBo"

# تهيئة كائن الاتصال للتعامل مع بروتوكولات الشبكة
bot = telebot.TeleBot(API_TOKEN)


# دالة لمعالجة الطلبات الواردة وتحليلها كبيانات شبكية
def process_network_request(chat_id, url_string):
    repo_pattern = re.match(r"https?://github\.com/([\w-]+)/([\w.-]+)/?$", url_string)
    file_pattern = re.match(r"https?://github\.com/([\w-]+)/([\w.-]+)/blob/(.+)", url_string)

    if repo_pattern:
        user, repo = repo_pattern.groups()
        handle_data_package(chat_id, user, repo)
    elif file_pattern:
        raw_url = url_string.replace("/blob/", "/raw/")
        handle_direct_stream(chat_id, raw_url)
    else:
        bot.send_message(chat_id, "⚠️ طلب غير صالح. يرجى استخدام عناوين من نطاق github.com فقط.")


# دالة للتعامل مع حزم البيانات (المستودعات) وتسميتها عند الإرسال
def handle_data_package(chat_id, user, repo):
    status_message = bot.send_message(chat_id, f"⏳ جارٍ تحضير حزمة البيانات من المصدر: {user}/{repo}")
    
    zip_url = f"https://github.com/{user}/{repo}/archive/refs/heads/main.zip"
    
    try:
        response = requests.get(zip_url, timeout=30)
        response.raise_for_status()

        in_memory_buffer = response.content
        
        bot.edit_message_text("✅ تم استقبال الحزمة. جارٍ إرسالها بالاسم المخصص...", chat_id, status_message.message_id)

        # -- هنا الحل الذكي --
        # نرسل البيانات من الذاكرة ونحدد اسم الملف الظاهري للمستخدم
        visible_filename = "MyRepo.zip"
        bot.send_document(chat_id, in_memory_buffer, visible_file_name=visible_filename, caption=f"تم تحميل المستودع كـ {visible_filename}")
        
        bot.delete_message(chat_id, status_message.message_id)

    except requests.exceptions.RequestException:
        bot.edit_message_text("❌ فشل الاتصال بالمصدر. قد يكون خاصًا أو غير موجود.", chat_id, status_message.message_id)


# دالة للتعامل مع الملفات المباشرة وتسميتها عند الإرسال
def handle_direct_stream(chat_id, url):
    original_filename = url.split('/')[-1]
    status_message = bot.send_message(chat_id, f"⏳ جارٍ جلب البيانات: {original_filename}")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        # -- هنا الحل الذكي --
        # نحدد اسمًا جديدًا مع الحفاظ على امتداد الملف الأصلي
        file_extension = ""
        if '.' in original_filename:
            file_extension = "." + original_filename.split('.')[-1]
        
        visible_filename = f"MyFile{file_extension}"
        
        bot.send_document(chat_id, response.content, visible_file_name=visible_filename, caption=f"تم تحميل الملف كـ {visible_filename}")
        bot.delete_message(chat_id, status_message.message_id)

    except requests.exceptions.RequestException:
        bot.edit_message_text("❌ فشل في جلب البيانات. تحقق من العنوان.", chat_id, status_message.message_id)


# معالج رسالة الترحيب
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "أهلاً بك في مساعد GitHub!\n\n"
        "أرسل لي رابط مستودع أو ملف من GitHub وسأقوم بتحميله لك بالاسم المخصص."
    )
    bot.reply_to(message, welcome_text)


# معالج جميع الرسائل النصية
@bot.message_handler(func=lambda message: True)
def message_listener(message):
    if "github.com" in message.text:
        process_network_request(message.chat.id, message.text.strip())


# بدء تشغيل البوت
print("Secure GitHub Bot is running...")
bot.infinity_polling()
