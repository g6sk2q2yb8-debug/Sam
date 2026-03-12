import telebot
import yt_dlp
import os
from telebot import types

# تم وضع التوكن الخاص بك هنا
TOKEN = "8647831819:AAFo8_JxQXN5uMAdIlN458ja1bsL_G15q94"
bot = telebot.TeleBot(TOKEN)

# --- قاعدة بيانات المسلسلات ---
series_db = {
    "مسلسل نهار": {
        "الحلقة 1": "ضع_الـ_ID_هنا",
    }
}

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for s_name in series_db.keys():
        markup.add(types.InlineKeyboardButton(s_name, callback_data=f"list_{s_name}"))
    
    welcome_text = (
        "🎬 **مرحباً بك في بوت ذكريات نهار**\n\n"
        "أنا مساعدك التقني، يمكنك:\n"
        "1️⃣ اختيار مسلسل من القائمة أدناه.\n"
        "2️⃣ إرسال رابط يوتيوب ليتم تحميله تلقائياً."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('list_'))
def list_episodes(call):
    s_name = call.data.split('_')[1]
    episodes = series_db[s_name]
    markup = types.InlineKeyboardMarkup(row_width=2)
    for ep_name in episodes.keys():
        markup.add(types.InlineKeyboardButton(ep_name, callback_data=f"play_{s_name}_{ep_name}"))
    markup.add(types.InlineKeyboardButton("⬅️ العودة للقائمة", callback_data="back_to_main"))
    bot.edit_message_text(f"📺 {s_name}\nاختر الحلقة:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_main(call):
    send_welcome(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('play_'))
def play_video(call):
    data = call.data.split('_')
    s_name, ep_name = data[1], data[2]
    v_id = series_db[s_name][ep_name]
    
    if v_id == "ضع_الـ_ID_هنا":
        bot.answer_callback_query(call.id, "❌ لم يتم رفع الفيديو لهذه الحلقة بعد.")
    else:
        bot.answer_callback_query(call.id, "⏳ جاري إرسال الفيديو...")
        bot.send_video(call.message.chat.id, v_id, caption=f"🎬 {s_name} - {ep_name}")

@bot.message_handler(func=lambda message: 'youtube.com' in message.text or 'youtu.be' in message.text)
def handle_youtube(message):
    wait_msg = bot.reply_to(message, "⏳ جاري سحب الفيديو من يوتيوب بأعلى جودة ممكنة... قد يستغرق ذلك بعض الوقت.")
    downloaded_file = None
    try:
        # خيارات yt-dlp لتحميل أعلى جودة ممكنة
        # 'bestvideo+bestaudio/best' سيحاول دمج أفضل فيديو وأفضل صوت
        # 'merge_output_format': 'mp4' لضمان أن يكون الإخراج بصيغة mp4
        # 'outtmpl': 'downloads/%(title)s.%(ext)s' لحفظ الملفات في مجلد 'downloads' باسم الفيديو الأصلي
        # 'noplaylist': True لمنع تحميل قوائم التشغيل بالكامل
        # 'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}] لضمان التحويل إلى mp4 إذا لزم الأمر
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }],
        }

        # إنشاء مجلد التحميلات إذا لم يكن موجوداً
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(message.text, download=True)
            downloaded_file = ydl.prepare_filename(info_dict)

        if downloaded_file and os.path.exists(downloaded_file):
            file_size = os.path.getsize(downloaded_file)
            # Telegram bot API limits: 50MB for video, 2GB for document
            # Convert bytes to MB for comparison
            file_size_mb = file_size / (1024 * 1024)

            if file_size_mb <= 50:
                bot.edit_message_text("✅ تم التحميل بنجاح! جاري إرسال الفيديو...", message.chat.id, wait_msg.message_id)
                with open(downloaded_file, 'rb') as video:
                    sent = bot.send_video(message.chat.id, video, caption="✅ تم التحميل بنجاح!")
                    bot.send_message(message.chat.id, f"معرف الفيديو (file_id) لإضافته للقائمة:\n\n`{sent.video.file_id}`", parse_mode="Markdown")
            elif file_size_mb <= 2000:
                bot.edit_message_text("✅ تم التحميل بنجاح! حجم الفيديو كبير، جاري إرساله كمستند...", message.chat.id, wait_msg.message_id)
                with open(downloaded_file, 'rb') as doc:
                    sent = bot.send_document(message.chat.id, doc, caption="✅ تم التحميل بنجاح!")
                    # Documents don't always have a 'video' attribute, so we check 'document'
                    file_id_to_save = sent.document.file_id if hasattr(sent, 'document') else "N/A"
                    bot.send_message(message.chat.id, f"معرف الملف (file_id) لإضافته للقائمة:\n\n`{file_id_to_save}`", parse_mode="Markdown")
            else:
                bot.edit_message_text(f"❌ حجم الفيديو يتجاوز الحد المسموح به (2GB). لا يمكن إرساله.", message.chat.id, wait_msg.message_id)
        else:
            bot.edit_message_text("❌ لم يتم العثور على الملف المحمل.", message.chat.id, wait_msg.message_id)

    except yt_dlp.DownloadError as e:
        bot.edit_message_text(f"❌ حدث خطأ أثناء التحميل من يوتيوب: {str(e)}", message.chat.id, wait_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ غير متوقع: {str(e)}", message.chat.id, wait_msg.message_id)
    finally:
        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        bot.delete_message(message.chat.id, wait_msg.message_id)

print("✅ البوت شغال الآن بالتوكن الخاص بك!")
bot.infinity_polling()
