import html
from typing import Dict, Any, Optional

SUPPORTED_LANGUAGES = {
    "uz": "🇺🇿 O‘zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

DEFAULT_LANGUAGE = "uz"

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "uz": {
        # --- Reply Keyboards ---
        "btn_pro": "💎 PRO Obuna",
        "btn_status": "🛡 Holat",
        "btn_settings": "⚙️ Sozlamalar",
        "btn_language": "🌐 Til",
        "btn_help": "ℹ️ Yordam",
        
        # --- Inline Buttons ---
        "btn_back": "🔙 Orqaga",
        "btn_main_menu": "🔙 Asosiy menyu",
        "btn_connect_guide": "⚡ Ulanish yo‘riqnomasi",
        "btn_pro_plans": "💎 PRO Tariflar (Stars)",
        "btn_about": "ℹ️ Bot haqida",
        "btn_activate_pro": "⭐ PRO’ni faollashtirish (50 Stars)",
        "btn_disable_autorenew": "❌ Avtomatik uzaytirishni o‘chirish",
        "btn_enable_autorenew": "🔄 Avtomatik uzaytirishni yoqish",
        "btn_change_lang": "🌐 Tilni o‘zgartirish",
        "btn_delete_my_data": "🗑 Ma'lumotlarimni o‘chirish",
        "btn_cancel": "❌ Bekor qilish",
        "btn_confirm_delete": "🗑 Ha, barchasini o‘chirish",
        "btn_prev": "⬅️ Oldingi",
        "btn_next": "Keyingi ➡️",
        
        # --- Settings items ---
        "toggle_deleted_text": "🗑 O‘chirilgan matn",
        "toggle_edited_messages": "✏️ Tahrirlangan xabarlar",
        "toggle_deleted_photos": "📷 O‘chirilgan rasmlar",
        "toggle_deleted_videos": "🎥 O‘chirilgan videolar",
        "toggle_deleted_voice": "🎙 O‘chirilgan ovozlar",
        "toggle_all_notifications": "🔔 Barcha bildirishnomalar",
        "status_on": "ON",
        "status_off": "OFF",
        
        # --- Start & Onboarding ---
        "start_welcome": (
            "✦ <b>REWIND BOT</b> ✦\n\n"
            "Telegram shaxsiy chatlaringizdagi <b>o‘chirilgan</b>, <b>tahrirlangan</b> va <b>bir martalik (View-Once)</b> medialarni xavfsiz arxivlang.\n\n"
            "<blockquote>🎁 <b>3 kunlik to‘liq bepul PRO sinov muddati</b>\n"
            "⭐ Keyin <code>50 Stars / 30 kun</code></blockquote>\n\n"
            "<i>Botni shaxsiy chatlaringizga ulash uchun quyidagi tugmani bosing:</i>"
        ),
        "start_bottom_hint": "Quyidagi menyu orqali boshqarishingiz mumkin:",
        "start_guide": (
            "⚡ <b>Telegram Business Botni ulash yo‘riqnomasi:</b>\n\n"
            "1️⃣ Telegram <b>Sozlamalar (Settings)</b> ga kiring.\n"
            "2️⃣ <b>Telegram Business</b> bo‘limini tanlang.\n"
            "3️⃣ <b>Chat Automation (Chatlar avtomatizatsiyasi)</b> / <b>Bots</b> bo‘limiga kiring.\n"
            "4️⃣ Bizning botimizni (<code>@{bot_username}</code>) tanlang va barcha ruxsatlarni bering.\n\n"
            "<blockquote>🎉 Ruxsat berilgan zahoti sizga <b>72 soatlik bepul PRO sinov</b> avtomatik faollashadi!</blockquote>"
        ),
        
        # --- Status ---
        "status_title": "🛡 <b>Tizim Holati va Monitoring</b>",
        "status_business": "Telegram Business",
        "status_monitoring": "Xabarlar monitoringi",
        "status_current_plan": "Joriy tarif",
        "status_expiration": "Amal qilish muddati",
        "status_active": "🟢 Faol",
        "status_not_connected": "🔴 Ulanmagan",
        "status_monitored": "🟢 Kuzatilmoqda",
        "status_paused": "🔴 To‘xtatilgan",
        "status_trial": "🎁 Bepul sinov (Trial)",
        "status_pro_active": "💎 PRO Obuna (Faol)",
        "status_expired": "❌ Muddati tugagan",
        "status_na": "Mavjud emas",
        "status_archive_stat": "🗑 <b>Arxivda jami saqlangan:</b> <code>{count}</code> ta o‘chirilgan xabarlar",
        
        # --- Help ---
        "help_title": "ℹ️ <b>Rewind Bot — Foydalanish Qo‘llanmasi</b>",
        "help_text": (
            "ℹ️ <b>Rewind Bot Haqida Ma'lumot</b>\n\n"
            "<blockquote>"
            "• <b>Qanday ishlaydi?</b> Bot Telegram Business ulanishi orqali shaxsiy chatlaringizdagi xabarlar tarixini xavfsiz arxivlaydi.\n"
            "• <b>O‘chirilgan xabarlar:</b> Suhbatdoshingiz xabarni o‘chirsa, bot darhol sizga uning asl matni yoki rasmini yuboradi.\n"
            "• <b>Tahrirlangan xabarlar:</b> Xabar o‘zgartirilsa, eski va yangi variantlarini solishtirib beradi.\n"
            "• <b>View-Once media:</b> O‘chib ketuvchi rasm, ovozli va video xabarlar reply qilinganda yoki o‘chirilganda to‘liq ochib beriladi.\n"
            "• <b>Xavfsizlik:</b> Barcha ma'lumotlar shaxsiy hisobingizga biriktirilgan va uchinchi shaxslarga berilmaydi."
            "</blockquote>"
        ),
        
        # --- Language ---
        "lang_select_title": "🌐 <b>Tilni tanlang / Выберите язык / Choose language:</b>",
        "lang_changed": "✅ Til <b>O‘zbekcha</b>ga o‘zgartirildi.",
        
        # --- Settings ---
        "settings_title": (
            "⚙️ <b>Bildirishnoma va Xavfsizlik Sozlamalari</b>\n\n"
            "Quyidagi tugmalar orqali qaysi turdagi xabarlar uchun bildirishnoma olishni xohlashingizni sozlashingiz mumkin:"
        ),
        "settings_updated": "Sozlama yangilandi.",
        "delete_data_confirm": (
            "⚠️ <b>Diqqat! Ma'lumotlarni o‘chirish</b>\n\n"
            "Sizning barcha saqlangan xabarlaringiz, tahrirlar tarixi, media arxiv va sozlamalaringiz "
            "<b>butunlay va qaytarib bo‘lmas darajada</b> o‘chiriladi.\n\n"
            "Haqiqatan ham barcha ma'lumotlaringizni o‘chirmoqchimisiz?"
        ),
        "delete_data_success": "✅ <b>Barcha shaxsiy ma'lumotlaringiz va media arxivlaringiz to‘liq o‘chirildi.</b>",
        "delete_data_error": "❌ Ma'lumotlarni o‘chirishda xatolik yuz berdi. Iltimos qayta urinib ko‘ring.",
        
        # --- Subscription / PRO ---
        "pro_title": "💎 <b>Rewind PRO Obunasi</b>",
        "pro_status_label": "📊 Joriy holat:",
        "pro_features": (
            "<blockquote><b>PRO imkoniyatlari:</b>\n"
            "• Cheksiz o‘chirilgan xabarlarni saqlash\n"
            "• Barcha turdagi mediani (rasm, video, ovoz) arxivlash\n"
            "• Bir martalik (View-Once) medialarni ochish\n"
            "• Tahrirlangan xabarlarni solishtirish</blockquote>\n\n"
            "⭐ <b>Tarif:</b> <code>50 Stars</code> / 30 kun"
        ),
        "invoice_title": "Rewind PRO Obunasi",
        "invoice_description": "Telegram shaxsiy chatlaringizdagi barcha o‘chirilgan va tahrirlangan xabarlarni 30 kun davomida to‘liq arxivlash va ko‘rish imkoniyati.",
        "invoice_price_label": "Rewind PRO — 30 kun",
        "invoice_error": "Invoice yaratishda xatolik yuz berdi. Iltimos qayta urinib ko‘ring.",
        "pre_checkout_error_currency": "Faqat Telegram Stars qabul qilinadi.",
        "pre_checkout_error_amount": "To‘lov miqdori noto‘g‘ri.",
        "payment_success": (
            "🎉 <b>To‘lovingiz qabul qilindi!</b>\n\n"
            "⭐ <b>50 Stars</b> muvaffaqiyatli to‘landi.\n"
            "💎 <b>Rewind PRO</b> obunangiz <b>{exp_date}</b> gacha faol etildi!\n\n"
            "<i>Xabarlar monitoringi uzluksiz davom etadi.</i>"
        ),
        
        # --- Business Connection ---
        "conn_connected_trial": (
            "🎉 <b>Telegram Business muvaffaqiyatli ulandi!</b>\n\n"
            "<blockquote>🎁 Siz uchun <b>72 soatlik (3 kun) to‘liq bepul PRO sinov muddati</b> boshlandi!</blockquote>\n\n"
            "<i>Endi shaxsiy chatlaringizdagi o‘chirilgan, tahrirlangan va bir martalik (View-Once) xabarlar shu yerda aks etadi.</i>"
        ),
        "conn_reconnected": "✅ <b>Telegram Business ulanishi qayta faollashtirildi!</b>",
        "conn_disconnected": "⚠️ <b>Telegram Business ulanishi uzildi.</b> Monitoring to‘xtatildi.",
        
        # --- Notifications ---
        "deleted_text_title": "🗑 <b>O‘chirilgan xabar</b>",
        "deleted_text_edited_note": "(<i>tahrirlangan</i>)",
        "deleted_media_title": "🗑 <b>O‘chirilgan {media_type}</b>",
        "deleted_missing_text": (
            "🗑 <b>{count} ta xabar o‘chirilgani aniqlandi.</b>\n\n"
            "⚠️ <i>Xabarlarning mazmuni arxivda mavjud emas (bot ulanishidan avval yozilgan bo‘lishi mumkin).</i>"
        ),
        "edited_msg_title": "✏️ <b>Tahrirlangan xabar</b>",
        "edited_old_label": "⏱ <b>Oldingi:</b>",
        "edited_new_label": "✨ <b>Yangi:</b>",
        "view_once_title": "👁 <b>View-Once media ochildi</b>",
        "media_fetch_error": "⚠️ <i>(Media fayl yuklab olinmadi)</i>",
        
        # --- Media Type Names ---
        "media_photo": "rasm",
        "media_video": "video",
        "media_voice": "ovozli xabar",
        "media_video_note": "video xabar",
        "media_document": "fayl",
        "media_audio": "audio",
        "media_animation": "GIF",
        "media_generic": "media",
        "sender_user": "Foydalanuvchi",
        "sender_partner": "Suhbatdosh",
        "initial_text": "(Boshlang‘ich matn)",
        
        # --- Scheduler & Expiration Alerts ---
        "trial_reminder_24h": (
            "⏳ <b>PRO sinov muddati ertaga tugaydi!</b>\n\n"
            "Xabarlar arxivini uzluksiz saqlash uchun PRO obunani faollashtiring:\n"
            "⭐ <b>50 Stars / 30 kun</b>\n\n"
            "<i>Faollashtirish uchun: /pro</i>"
        ),
        "sub_expired_alert": (
            "⚠️ <b>PRO Obuna / Sinov muddati tugagan!</b>\n\n"
            "<blockquote>Sizning Telegram chatlaringizdagi xabarlar monitoringi to‘xtatildi.\n"
            "O‘chirilgan va tahrirlangan xabarlarni qaytarish, View-Once medialarni ochish uchun PRO obunangizni faollashtiring.</blockquote>\n\n"
            "⭐ <b>Tarif:</b> <code>50 Stars / 30 kun</code>\n"
            "👉 <b>Faollashtirish uchun:</b> /pro"
        ),
        "pro_granted_user": (
            "🎉 <b>Sizga PRO Obuna taqdim etildi!</b>\n\n"
            "<blockquote>💎 Administrator tomonidan sizga <b>{days} kunlik</b> bepul PRO obunasi taqdim etildi!\n"
            "Barcha xabarlar monitoringi va arxivlash imkoniyatlari to‘liq faollashtirildi.</blockquote>\n\n"
            "📅 <b>Amal qilish muddati:</b> <code>{exp_date}</code>"
        ),
        "pro_revoked_user": "⚠️ Sizning PRO obunangiz bekor qilindi.",
        "admin_added_user": "⭐️ <b>Sizga Rewind Bot administratorlik huquqi berildi!</b>\n\nBoshqaruv paneli: /admin",
        "admin_removed_user": "ℹ️ Sizning administratorlik huquqingiz bekor qilindi.",
    },

    "ru": {
        # --- Reply Keyboards ---
        "btn_pro": "💎 PRO Подписка",
        "btn_status": "🛡 Статус",
        "btn_settings": "⚙️ Настройки",
        "btn_language": "🌐 Язык",
        "btn_help": "ℹ️ Помощь",
        
        # --- Inline Buttons ---
        "btn_back": "🔙 Назад",
        "btn_main_menu": "🔙 Главное меню",
        "btn_connect_guide": "⚡ Инструкция по подключению",
        "btn_pro_plans": "💎 PRO Тарифы (Stars)",
        "btn_about": "ℹ️ О боте",
        "btn_activate_pro": "⭐ Активировать PRO (50 Stars)",
        "btn_disable_autorenew": "❌ Отключить автопродление",
        "btn_enable_autorenew": "🔄 Включить автопродление",
        "btn_change_lang": "🌐 Сменить язык",
        "btn_delete_my_data": "🗑 Удалить мои данные",
        "btn_cancel": "❌ Отмена",
        "btn_confirm_delete": "🗑 Да, удалить всё",
        "btn_prev": "⬅️ Назад",
        "btn_next": "Вперед ➡️",
        
        # --- Settings items ---
        "toggle_deleted_text": "🗑 Текстовые сообщения",
        "toggle_edited_messages": "✏️ Измененные сообщения",
        "toggle_deleted_photos": "📷 Фотографии",
        "toggle_deleted_videos": "🎥 Видеозаписи",
        "toggle_deleted_voice": "🎙 Голосовые сообщения",
        "toggle_all_notifications": "🔔 Все уведомления",
        "status_on": "ВКЛ",
        "status_off": "ВЫКЛ",
        
        # --- Start & Onboarding ---
        "start_welcome": (
            "✦ <b>REWIND BOT</b> ✦\n\n"
            "Безопасный архив <b>удаленных</b>, <b>отредактированных</b> и <b>одноразовых (View-Once)</b> сообщений в личных чатах Telegram.\n\n"
            "<blockquote>🎁 <b>3 дня бесплатного полного PRO-периода</b>\n"
            "⭐ Далее <code>50 Stars / 30 дней</code></blockquote>\n\n"
            "<i>Чтобы подключить бота к вашим личным чатам, нажмите кнопку ниже:</i>"
        ),
        "start_bottom_hint": "Используйте меню ниже для управления ботом:",
        "start_guide": (
            "⚡ <b>Инструкция по подключению Telegram Business:</b>\n\n"
            "1️⃣ Откройте <b>Настройки (Settings)</b> Telegram.\n"
            "2️⃣ Перейдите в раздел <b>Telegram Business</b>.\n"
            "3️⃣ Выберите <b>Chat Automation (Чат-боты)</b> / <b>Bots</b>.\n"
            "4️⃣ Выберите нашего бота (<code>@{bot_username}</code>) и предоставьте разрешения.\n\n"
            "<blockquote>🎉 Сразу после подключения вам автоматически активируется <b>бесплатный PRO-период на 72 часа</b>!</blockquote>"
        ),
        
        # --- Status ---
        "status_title": "🛡 <b>Статус системы и мониторинг</b>",
        "status_business": "Telegram Business",
        "status_monitoring": "Мониторинг сообщений",
        "status_current_plan": "Текущий тариф",
        "status_expiration": "Срок действия",
        "status_active": "🟢 Активен",
        "status_not_connected": "🔴 Не подключен",
        "status_monitored": "🟢 Отслеживается",
        "status_paused": "🔴 Приостановлен",
        "status_trial": "🎁 Пробный период (Trial)",
        "status_pro_active": "💎 PRO Подписка (Активна)",
        "status_expired": "❌ Истек",
        "status_na": "Недоступно",
        "status_archive_stat": "🗑 <b>Всего сохранено в архиве:</b> <code>{count}</code> удаленных сообщений",
        
        # --- Help ---
        "help_title": "ℹ️ <b>Rewind Bot — Руководство пользователя</b>",
        "help_text": (
            "ℹ️ <b>О сервисе Rewind Bot</b>\n\n"
            "<blockquote>"
            "• <b>Как это работает?</b> Через подключение Telegram Business бот безопасно архивирует историю сообщений ваших личных чатов.\n"
            "• <b>Удаленные сообщения:</b> Если собеседник удалит сообщение, бот мгновенно отправит вам его исходный текст или медиа.\n"
            "• <b>Отредактированные сообщения:</b> При изменении сообщения бот покажет сравнение старого и нового текста.\n"
            "• <b>View-Once медиа:</b> Одноразовые фото, видео и голосовые мгновенно сохраняются и открываются при ответе (Reply) или удалении.\n"
            "• <b>Конфиденциальность:</b> Все данные строго привязаны к вашему аккаунту и не передаются третьим лицам."
            "</blockquote>"
        ),
        
        # --- Language ---
        "lang_select_title": "🌐 <b>Выберите язык / Choose language / Tilni tanlang:</b>",
        "lang_changed": "✅ Язык успешно изменен на <b>Русский</b>.",
        
        # --- Settings ---
        "settings_title": (
            "⚙️ <b>Настройки уведомлений и приватности</b>\n\n"
            "С помощью кнопок ниже вы можете настроить, для каких типов событий вы хотите получать уведомления:"
        ),
        "settings_updated": "Настройка обновлена.",
        "delete_data_confirm": (
            "⚠️ <b>Внимание! Удаление данных</b>\n\n"
            "Все ваши сохраненные сообщения, история правок, медиа-архив и персональные настройки будут "
            "<b>безвозвратно и полностью</b> удалены.\n\n"
            "Вы действительно хотите удалить все свои данные?"
        ),
        "delete_data_success": "✅ <b>Все ваши персональные данные и медиа-архив успешно удалены.</b>",
        "delete_data_error": "❌ Ошибка при удалении данных. Пожалуйста, попробуйте позже.",
        
        # --- Subscription / PRO ---
        "pro_title": "💎 <b>Подписка Rewind PRO</b>",
        "pro_status_label": "📊 Текущий статус:",
        "pro_features": (
            "<blockquote><b>Преимущества PRO:</b>\n"
            "• Неограниченное сохранение удаленных сообщений\n"
            "• Архивация всех типов медиа (фото, видео, голосовые)\n"
            "• Мгновенный просмотр одноразовых (View-Once) медиа\n"
            "• Сравнение истории правок сообщений</blockquote>\n\n"
            "⭐ <b>Тариф:</b> <code>50 Stars</code> / 30 дней"
        ),
        "invoice_title": "Подписка Rewind PRO",
        "invoice_description": "Полный доступ к архивации и просмотру удаленных и измененных сообщений в личных чатах Telegram на 30 дней.",
        "invoice_price_label": "Rewind PRO — 30 дней",
        "invoice_error": "Ошибка при создании счета. Пожалуйста, попробуйте еще раз.",
        "pre_checkout_error_currency": "Принимаются только Telegram Stars.",
        "pre_checkout_error_amount": "Неверная сумма платежа.",
        "payment_success": (
            "🎉 <b>Оплата успешно принята!</b>\n\n"
            "⭐ <b>50 Stars</b> успешно оплачены.\n"
            "💎 Ваша подписка <b>Rewind PRO</b> активна до <b>{exp_date}</b>!\n\n"
            "<i>Мониторинг сообщений продолжается без перебоев.</i>"
        ),
        
        # --- Business Connection ---
        "conn_connected_trial": (
            "🎉 <b>Telegram Business успешно подключен!</b>\n\n"
            "<blockquote>🎁 Вам активирован <b>бесплатный пробный PRO-период на 72 часа (3 дня)</b>!</blockquote>\n\n"
            "<i>Теперь все удаленные, измененные и View-Once сообщения из ваших чатов будут приходить сюда.</i>"
        ),
        "conn_reconnected": "✅ <b>Подключение Telegram Business снова активно!</b>",
        "conn_disconnected": "⚠️ <b>Подключение Telegram Business разорвано.</b> Мониторинг приостановлен.",
        
        # --- Notifications ---
        "deleted_text_title": "🗑 <b>Удаленное сообщение</b>",
        "deleted_text_edited_note": "(<i>изменено</i>)",
        "deleted_media_title": "🗑 <b>Удаленное {media_type}</b>",
        "deleted_missing_text": (
            "🗑 <b>Обнаружено удаление {count} сообщений.</b>\n\n"
            "⚠️ <i>Содержимое отсутствует в архиве (возможно, было отправлено до подключения бота).</i>"
        ),
        "edited_msg_title": "✏️ <b>Отредактированное сообщение</b>",
        "edited_old_label": "⏱ <b>Было:</b>",
        "edited_new_label": "✨ <b>Стало:</b>",
        "view_once_title": "👁 <b>Открыто View-Once медиа</b>",
        "media_fetch_error": "⚠️ <i>(Не удалось загрузить медиа-файл)</i>",
        
        # --- Media Type Names ---
        "media_photo": "фото",
        "media_video": "видео",
        "media_voice": "голосовое сообщение",
        "media_video_note": "видеосообщение",
        "media_document": "документ",
        "media_audio": "аудио",
        "media_animation": "GIF",
        "media_generic": "медиа",
        "sender_user": "Пользователь",
        "sender_partner": "Собеседник",
        "initial_text": "(Исходный текст)",
        
        # --- Scheduler & Expiration Alerts ---
        "trial_reminder_24h": (
            "⏳ <b>Пробный PRO-период заканчивается завтра!</b>\n\n"
            "Чтобы архив сообщений продолжал работать без перебоев, активируйте PRO:\n"
            "⭐ <b>50 Stars / 30 дней</b>\n\n"
            "<i>Для активации: /pro</i>"
        ),
        "sub_expired_alert": (
            "⚠️ <b>Подписка PRO / Пробный период истек!</b>\n\n"
            "<blockquote>Мониторинг сообщений в ваших чатах приостановлен.\n"
            "Чтобы восстанавливать удаленные и измененные сообщения, а также открывать View-Once медиа, активируйте PRO подписку.</blockquote>\n\n"
            "⭐ <b>Тариф:</b> <code>50 Stars / 30 дней</code>\n"
            "👉 <b>Для активации:</b> /pro"
        ),
        "pro_granted_user": (
            "🎉 <b>Вам предоставлена PRO Подписка!</b>\n\n"
            "<blockquote>💎 Администратор предоставил вам бесплатную PRO подписку на <b>{days} дн.</b>!\n"
            "Все функции архивации и мониторинга сообщений полностью активны.</blockquote>\n\n"
            "📅 <b>Срок действия:</b> <code>{exp_date}</code>"
        ),
        "pro_revoked_user": "⚠️ Ваша подписка PRO была отозвана.",
        "admin_added_user": "⭐️ <b>Вам выданы права администратора Rewind Bot!</b>\n\nПанель управления: /admin",
        "admin_removed_user": "ℹ️ Ваши права администратора были отозваны.",
    },

    "en": {
        # --- Reply Keyboards ---
        "btn_pro": "💎 PRO Subscription",
        "btn_status": "🛡 Status",
        "btn_settings": "⚙️ Settings",
        "btn_language": "🌐 Language",
        "btn_help": "ℹ️ Help",
        
        # --- Inline Buttons ---
        "btn_back": "🔙 Back",
        "btn_main_menu": "🔙 Main menu",
        "btn_connect_guide": "⚡ Connection Guide",
        "btn_pro_plans": "💎 PRO Plans (Stars)",
        "btn_about": "ℹ️ About bot",
        "btn_activate_pro": "⭐ Activate PRO (50 Stars)",
        "btn_disable_autorenew": "❌ Disable auto-renewal",
        "btn_enable_autorenew": "🔄 Enable auto-renewal",
        "btn_change_lang": "🌐 Change language",
        "btn_delete_my_data": "🗑 Delete my data",
        "btn_cancel": "❌ Cancel",
        "btn_confirm_delete": "🗑 Yes, delete all",
        "btn_prev": "⬅️ Previous",
        "btn_next": "Next ➡️",
        
        # --- Settings items ---
        "toggle_deleted_text": "🗑 Text messages",
        "toggle_edited_messages": "✏️ Edited messages",
        "toggle_deleted_photos": "📷 Photos",
        "toggle_deleted_videos": "🎥 Videos",
        "toggle_deleted_voice": "🎙 Voice messages",
        "toggle_all_notifications": "🔔 All notifications",
        "status_on": "ON",
        "status_off": "OFF",
        
        # --- Start & Onboarding ---
        "start_welcome": (
            "✦ <b>REWIND BOT</b> ✦\n\n"
            "Securely archive <b>deleted</b>, <b>edited</b>, and <b>View-Once</b> media messages in your private Telegram chats.\n\n"
            "<blockquote>🎁 <b>3-day full PRO free trial</b>\n"
            "⭐ Then <code>50 Stars / 30 days</code></blockquote>\n\n"
            "<i>To connect the bot to your private chats, tap the button below:</i>"
        ),
        "start_bottom_hint": "Use the menu below to manage your preferences:",
        "start_guide": (
            "⚡ <b>Telegram Business Connection Guide:</b>\n\n"
            "1️⃣ Open Telegram <b>Settings</b>.\n"
            "2️⃣ Go to <b>Telegram Business</b>.\n"
            "3️⃣ Tap <b>Chat Automation</b> / <b>Bots</b>.\n"
            "4️⃣ Select our bot (<code>@{bot_username}</code>) and grant all permissions.\n\n"
            "<blockquote>🎉 As soon as connected, your <b>72-hour free PRO trial</b> activates automatically!</blockquote>"
        ),
        
        # --- Status ---
        "status_title": "🛡 <b>System Status & Monitoring</b>",
        "status_business": "Telegram Business",
        "status_monitoring": "Message monitoring",
        "status_current_plan": "Current plan",
        "status_expiration": "Expiration date",
        "status_active": "🟢 Active",
        "status_not_connected": "🔴 Disconnected",
        "status_monitored": "🟢 Monitoring",
        "status_paused": "🔴 Paused",
        "status_trial": "🎁 Free Trial",
        "status_pro_active": "💎 PRO Active",
        "status_expired": "❌ Expired",
        "status_na": "N/A",
        "status_archive_stat": "🗑 <b>Total saved in archive:</b> <code>{count}</code> deleted messages",
        
        # --- Help ---
        "help_title": "ℹ️ <b>Rewind Bot — User Guide</b>",
        "help_text": (
            "ℹ️ <b>About Rewind Bot</b>\n\n"
            "<blockquote>"
            "• <b>How it works:</b> Connected via Telegram Business, the bot securely archives message history from your private chats.\n"
            "• <b>Deleted messages:</b> If a contact deletes a message, the bot immediately delivers its original text or media here.\n"
            "• <b>Edited messages:</b> When a message is modified, the bot provides a side-by-side comparison of old and new text.\n"
            "• <b>View-Once media:</b> Disappearing photos, voice, and video notes are instantly recovered upon reply or deletion.\n"
            "• <b>Privacy:</b> All data is securely tied to your account and never shared with third parties."
            "</blockquote>"
        ),
        
        # --- Language ---
        "lang_select_title": "🌐 <b>Choose language / Tilni tanlang / Выберите язык:</b>",
        "lang_changed": "✅ Language successfully set to <b>English</b>.",
        
        # --- Settings ---
        "settings_title": (
            "⚙️ <b>Notification & Privacy Settings</b>\n\n"
            "Toggle which types of message events you want to receive notifications for:"
        ),
        "settings_updated": "Setting updated.",
        "delete_data_confirm": (
            "⚠️ <b>Warning! Permanent Data Deletion</b>\n\n"
            "All your archived messages, edit history, media files, and settings will be "
            "<b>permanently and irreversibly deleted</b>.\n\n"
            "Are you sure you want to delete all your data?"
        ),
        "delete_data_success": "✅ <b>All your personal data and media archives have been permanently deleted.</b>",
        "delete_data_error": "❌ An error occurred while deleting your data. Please try again.",
        
        # --- Subscription / PRO ---
        "pro_title": "💎 <b>Rewind PRO Subscription</b>",
        "pro_status_label": "📊 Current status:",
        "pro_features": (
            "<blockquote><b>PRO Features:</b>\n"
            "• Unlimited deleted message archive\n"
            "• Archiving for all media types (photos, videos, voice)\n"
            "• Instant view-once media recovery\n"
            "• Edit history diff comparison</blockquote>\n\n"
            "⭐ <b>Pricing:</b> <code>50 Stars</code> / 30 days"
        ),
        "invoice_title": "Rewind PRO Subscription",
        "invoice_description": "Full access to archiving and recovering deleted and edited messages in personal Telegram chats for 30 days.",
        "invoice_price_label": "Rewind PRO — 30 days",
        "invoice_error": "Failed to create invoice. Please try again.",
        "pre_checkout_error_currency": "Only Telegram Stars (XTR) are accepted.",
        "pre_checkout_error_amount": "Invalid payment amount.",
        "payment_success": (
            "🎉 <b>Payment Successful!</b>\n\n"
            "⭐ <b>50 Stars</b> received.\n"
            "💎 Your <b>Rewind PRO</b> subscription is active until <b>{exp_date}</b>!\n\n"
            "<i>Message monitoring is continuously running.</i>"
        ),
        
        # --- Business Connection ---
        "conn_connected_trial": (
            "🎉 <b>Telegram Business Connected Successfully!</b>\n\n"
            "<blockquote>🎁 Your <b>72-hour (3-day) full PRO free trial</b> has started!</blockquote>\n\n"
            "<i>Deleted, edited, and View-Once messages from your chats will now appear here.</i>"
        ),
        "conn_reconnected": "✅ <b>Telegram Business connection re-established!</b>",
        "conn_disconnected": "⚠️ <b>Telegram Business disconnected.</b> Monitoring paused.",
        
        # --- Notifications ---
        "deleted_text_title": "🗑 <b>Deleted Message</b>",
        "deleted_text_edited_note": "(<i>edited</i>)",
        "deleted_media_title": "🗑 <b>Deleted {media_type}</b>",
        "deleted_missing_text": (
            "🗑 <b>Detected {count} deleted messages.</b>\n\n"
            "⚠️ <i>Content not in archive (likely sent before the bot was connected).</i>"
        ),
        "edited_msg_title": "✏️ <b>Edited Message</b>",
        "edited_old_label": "⏱ <b>Original:</b>",
        "edited_new_label": "✨ <b>New edit:</b>",
        "view_once_title": "👁 <b>View-Once media opened</b>",
        "media_fetch_error": "⚠️ <i>(Could not retrieve media file)</i>",
        
        # --- Media Type Names ---
        "media_photo": "photo",
        "media_video": "video",
        "media_voice": "voice message",
        "media_video_note": "video message",
        "media_document": "document",
        "media_audio": "audio",
        "media_animation": "GIF",
        "media_generic": "media",
        "sender_user": "User",
        "sender_partner": "Contact",
        "initial_text": "(Initial text)",
        
        # --- Scheduler & Expiration Alerts ---
        "trial_reminder_24h": (
            "⏳ <b>Your PRO trial expires tomorrow!</b>\n\n"
            "Keep your message archive running uninterrupted by activating PRO:\n"
            "⭐ <b>50 Stars / 30 days</b>\n\n"
            "<i>To activate: /pro</i>"
        ),
        "sub_expired_alert": (
            "⚠️ <b>PRO Subscription / Free Trial Expired!</b>\n\n"
            "<blockquote>Message monitoring in your chats has been paused.\n"
            "To recover deleted and edited messages and view View-Once media, activate your PRO subscription.</blockquote>\n\n"
            "⭐ <b>Price:</b> <code>50 Stars / 30 days</code>\n"
            "👉 <b>To activate:</b> /pro"
        ),
        "pro_granted_user": (
            "🎉 <b>PRO Subscription Granted!</b>\n\n"
            "<blockquote>💎 An administrator has granted you a free PRO subscription for <b>{days} days</b>!\n"
            "Full message monitoring and archiving capabilities are now active.</blockquote>\n\n"
            "📅 <b>Expiration date:</b> <code>{exp_date}</code>"
        ),
        "pro_revoked_user": "⚠️ Your PRO subscription has been revoked.",
        "admin_added_user": "⭐️ <b>You have been granted Administrator rights for Rewind Bot!</b>\n\nAdmin panel: /admin",
        "admin_removed_user": "ℹ️ Your administrator rights have been revoked.",
    }
}


def normalize_language_code(lang_code: Optional[str]) -> str:
    """Normalizes Telegram language code to supported ('uz', 'ru', 'en')."""
    if not lang_code:
        return DEFAULT_LANGUAGE
    code = lang_code.lower().strip()
    if code.startswith("ru"):
        return "ru"
    if code.startswith("en"):
        return "en"
    if code.startswith("uz"):
        return "uz"
    return DEFAULT_LANGUAGE


def t(key: str, lang: Optional[str] = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """
    Retrieves localized string by key and language, interpolating kwargs.
    Falls back to default language or key name if missing.
    """
    lang = lang if (lang in TRANSLATIONS) else DEFAULT_LANGUAGE
    template = TRANSLATIONS.get(lang, {}).get(key)
    
    if template is None:
        template = TRANSLATIONS.get(DEFAULT_LANGUAGE, {}).get(key, key)

    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
