from film_config import api, token
import os
import openai
import telebot
import sqlite3
import time
from threading import Thread

bot = telebot.TeleBot(token)
r = 0


db = sqlite3.connect('film.db', check_same_thread = False) 
sql = db.cursor()

sql.execute("""CREATE TABLE IF NOT EXISTS film(
    name TEXT,
    same TEXT,
    stat INT
)""") 
db.commit()

openai.api_key = os.getenv("PROXY_API_KEY")
openai.api_base = "https://api.proxyapi.ru/openai/v1"



def answer(id,tex):
    global r
    try:
        client = openai.Client(
                        api_key=api,
                        base_url="https://api.proxyapi.ru/openai/v1",
                    )
        completion = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": f"Список из 50 фильмов похожих на фильм {tex}"
                            }
                        ]
                    )
        r +=1
        ans = completion.choices[0].message.content
        bot.send_message(id, ans)
        sql.execute(f"INSERT INTO film(name, same, stat) VALUES(?,?,?)",(tex, ans, 1))
        db.commit()
    except Exception:
        r+=2



@bot.message_handler(content_types=['text'])
def search(message):
    global r
    film_name = message.text
    if message.text == '/start':
        bot.send_message(message.chat.id, 'Привет, я - Фильмовский! Напиши мне название фильма, а я сделаю подборку похожих')
    elif message.text == '/statistika':
        test = list(sql.execute("SELECT name FROM film ORDER BY stat DESC"))
        test1 = list(sql.execute("SELECT stat FROM film ORDER BY stat DESC"))
        text = ''
        print(test)
        print(test1)
        for i in range(0, len(test)):
            text+=f'{test[i][0]} - {test1[i][0]}'+'\n'*2
        bot.send_message(message.chat.id, text)

    else:
        try:
            test = list(sql.execute("SELECT same FROM film WHERE name = (?)", (f'{film_name}',)))
            stat = list(sql.execute("SELECT stat FROM film WHERE name = (?)", (film_name,)))[0][0]
            print(stat)
            sql.execute("UPDATE film SET stat = (?) WHERE name = (?)", (stat+1, film_name,))
            test = test[0][0]   
            bot.send_message(message.chat.id, test)
            # print(0)
        except Exception:
            try:
                i = 0
                mess = bot.send_message(message.chat.id, f'Ваш запрос принят, ожидайте... {i}%')
                
                o = message.chat.id
                th = Thread(target=answer, args=(o,film_name))
                th.start()
                for i in range(1,101):
                    if r == 0:
                        bot.edit_message_text(chat_id=message.chat.id, message_id=mess.message_id, text=f'Ваш запрос принят, ожидайте... {str(i)}%')
                        time.sleep(1)
                    else:
                        r = 0
                        break

            except Exception:
                bot.send_message(message.chat.id, 'Произошла ошибка, но мы над ней уже работаем!!')





bot.infinity_polling(none_stop=True, timeout=50)