import telebot
from telebot import types
import sqlite3
from datetime import datetime, timedelta
import pytz
import time
import threading



bot = telebot.TeleBot('7683658457:AAHi8DMJb1snxTE0EKsVA89HR3VOI19-uvI', parse_mode='Markdown')                  



TIMEZONE = pytz.timezone('Europe/Moscow')




def get_db():                                                       #бд
    conn = sqlite3.connect('sirius_schedule.db', 
                         detect_types=sqlite3.PARSE_DECLTYPES,
                         check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


with get_db() as conn:                                                 #бд
    conn.execute("""
    CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        event_name TEXT NOT NULL,
        event_date TEXT NOT NULL,
        event_time TEXT NOT NULL,
        notified INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)


@bot.message_handler(commands=['start'])                       #приветственное сообщение, команда /start
def main(message):
    bot.send_message(message.chat.id, '''✨ *Добро пожаловать в мир организованного времени!* ✨

Приветствую тебя, друг! Я — твой цифровой ассистент, созданный чтобы превратить хаос расписания в идеальный порядок. 🌟

Представь: больше никаких забытых дедлайнов, пропущенных пар или внезапных "ой, а ведь сегодня же...". Я буду твоим персональным тайм-менеджером, напоминая о важном и храня все планы.

💡 *Секрет эффективности?* Просто нажми /help — и я раскрою все возможности, которые сделают твой день продуманным до минуты!

Готов начать путь к идеальной продуктивности? Команда /help — твой проводник! 🚀''')


@bot.message_handler(commands=['help'])                                                #команда /help
def help_command(message):
    bot.send_message(message.chat.id, '''📋 *Доступные команды:*

/start - Начало работы с ботом
/list - Все события с ID
/today - Показать расписание на сегодня
/tomorrow - Показать расписание на завтра
/week - Показать расписание на неделю
/add - Добавить новое событие
/schedule - Информационное сообщение о том, как добавить событие
/del - Удалить событие
/delschedule -  Информационное сообщение о том, как удалить событие
''')


@bot.message_handler(commands=['schedule'])                                                 #команда /schedule
def help_command(message):
    bot.send_message(message.chat.id, '''📝 *Формат добавления события:*
/add Название гггг-мм-дд чч:мм
Пример: /add Контрольная 2025-07-10 14:30
''')
    

@bot.message_handler(commands=['delschedule'])                                          #команда /delschedule
def help_command(message):
    bot.send_message(message.chat.id, '''🗑️ *Формат удаления:*
/del [ID]
Пример: /del 5
''')


@bot.message_handler(commands=['list'])                                  #команда /list
def handle_list(message):
    """Показать все события с их ID"""
    with get_db() as conn:
        events = conn.execute("""
            SELECT id, event_name, event_date, event_time 
            FROM schedule 
            WHERE user_id=?
            ORDER BY event_date, event_time
        """, (message.chat.id,)).fetchall()
    
    if not events:
        bot.send_message(message.chat.id, "ℹ️ У вас нет запланированных событий.")
        return
    
    response = "📋 *Ваши события:*\n\n"
    for event in events:
        response += f"ID: {event['id']}\n"
        response += f"• {event['event_date']} {event['event_time']} - {event['event_name']}\n\n"
    
    response += "Для удаления используйте /del [ID]"
    bot.send_message(message.chat.id, response)   


@bot.message_handler(commands=['today'])                                      #команда /today
def handle_today(message):
    today = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    with get_db() as conn:
        events = conn.execute("""
            SELECT event_name, event_time 
            FROM schedule 
            WHERE user_id=? AND event_date=?
            ORDER BY event_time
        """, (message.chat.id, today)).fetchall()
    
    response = "*📅 Расписание на сегодня:*\n\n"
    response += "\n".join(f"• {e['event_time']} - {e['event_name']}" for e in events) if events else "🎉 Свободный день!"
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['tomorrow'])                                       #команда /tomorrow
def handle_tomorrow(message):
    tomorrow = (datetime.now(TIMEZONE) + timedelta(days=1)).strftime("%Y-%m-%d")
    with get_db() as conn:
        events = conn.execute("""
            SELECT event_name, event_time 
            FROM schedule 
            WHERE user_id=? AND event_date=?
            ORDER BY event_time
        """, (message.chat.id, tomorrow)).fetchall()
    
    response = "*📅 Расписание на завтра:*\n\n"
    response += "\n".join(f"• {e['event_time']} - {e['event_name']}" for e in events) if events else "🎉 Свободный день!"
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['week'])                              #команда /week
def handle_week(message):
    today = datetime.now(TIMEZONE)
    week_later = today + timedelta(days=7)
    
    with get_db() as conn:
        events = conn.execute("""
            SELECT event_date, event_name, event_time 
            FROM schedule 
            WHERE user_id=? AND event_date BETWEEN ? AND ?
            ORDER BY event_date, event_time
        """, (message.chat.id, today.strftime("%Y-%m-%d"), week_later.strftime("%Y-%m-%d"))).fetchall()
    
    if not events:
        bot.send_message(message.chat.id, "🎉 На ближайшую неделю событий нет!")
        return
    
    response = "*📅 Расписание на неделю:*\n\n"
    current_date = None
    
    for event in events:
        if event['event_date'] != current_date:
            current_date = event['event_date']
            date_obj = datetime.strptime(current_date, "%Y-%m-%d")
            response += f"*{date_obj.strftime('%A, %d %B')}:*\n"
        response += f"• {event['event_time']} - {event['event_name']}\n"
    
    bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['add'])                      #комана add
def handle_add(message):
    try:
        parts = message.text.split(maxsplit=3)
        if len(parts) < 4:
            raise ValueError
        
        _, name, date, time = parts
        event_datetime = TIMEZONE.localize(
            datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        )
        
        if event_datetime < datetime.now(TIMEZONE):
            bot.send_message(message.chat.id, "❌ Нельзя добавить событие в прошлом!")
            return
            
        with get_db() as conn:
            conn.execute("""
                INSERT INTO schedule (user_id, event_name, event_date, event_time)
                VALUES (?, ?, ?, ?)
            """, (message.chat.id, name, date, time))
        
        bot.send_message(
            message.chat.id,
            f"✅ *{name}* успешно добавлено!\n"
            f"📅 *Дата:* {date}\n"
            f"⏰ *Время:* {time}\n\n"
            f"Я напомню за 1 час до события."
        )
    except ValueError:
        example_date = datetime.now(TIMEZONE).strftime('%Y-%m-%d')
        bot.send_message(
            message.chat.id,
            "❌ *Ошибка формата!*\n\n"
            "Используйте:\n"
            "`/add Название ГГГГ-ММ-ДД ЧЧ:ММ`\n\n"
            f"Пример: `/add Экзамен {example_date} 14:30`"
        )



@bot.message_handler(commands=['del'])                                     #команда del
def handle_delete(message):
    """Удалить событие по ID"""
    try:
        event_id = int(message.text.split()[1])
        
        with get_db() as conn:
            event = conn.execute("""
                SELECT id FROM schedule 
                WHERE id=? AND user_id=?
            """, (event_id, message.chat.id)).fetchone()
            
            if not event:
                bot.send_message(message.chat.id, "❌ Событие не найдено или вам не принадлежит!")
                return
            
            conn.execute("""
                DELETE FROM schedule 
                WHERE id=? AND user_id=?
            """, (event_id, message.chat.id))
            
        bot.send_message(message.chat.id, f"✅ Событие ID {event_id} успешно удалено!")
    
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "❌ Неверный формат! Используйте: /del [ID]\nПример: /del 5")



#напоминания
def reminder_worker():
    while True:
        try:
            now = datetime.now(TIMEZONE)
            reminder_time = now + timedelta(hours=1)
            
            with get_db() as conn:
                events = conn.execute("""
                    SELECT id, user_id, event_name, event_time
                    FROM schedule
                    WHERE event_date=? AND event_time=? AND notified=0
                """, (reminder_time.strftime("%Y-%m-%d"), 
                    reminder_time.strftime("%H:%M"))).fetchall()
                
                for event in events:
                    try:
                        bot.send_message(
                            event['user_id'],
                            f"🔔 *Напоминание!*\n\n"
                            f"Через час у вас запланировано:\n"
                            f"*{event['event_name']}* в {event['event_time']}\n\n"
                            f"Не забудьте подготовиться!"
                        )
                        conn.execute(
                            "UPDATE schedule SET notified=1 WHERE id=?",
                            (event['id'],)
                        )
                    except Exception as e:
                        print(f"Ошибка отправки: {e}")
            
            time.sleep(60)
        except Exception as e:
            print(f"Ошибка в работе напоминаний: {e}")
            time.sleep(300)





if __name__ == "__main__":
    threading.Thread(
        target=reminder_worker,
        daemon=True,
        name="ReminderWorker"
    ).start()
    
    print("Бот успешно запущен! Время Сочи:", datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M'))
    bot.infinity_polling()