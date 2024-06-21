import telebot, os, sys, psycopg2
from telebot.types import Message
from dotenv import load_dotenv
load_dotenv()


bot = telebot.TeleBot(os.getenv("TOKEN_BOT"))


try:
    connection = psycopg2.connect(
        database="postgres",
        user="postgres",
        password="postgres",
        host="postgres",
        port="5432",
    )

    cursor = connection.cursor()
    print("Успешное подключение к БД!")
except (Exception, psycopg2.Error) as e:
    print("Не удалось подключиться к БД\nОшибка:", e)
    sys.exit()


try:
    cursor.execute("""create table users
                   (id serial primary key,
                   user_id bigserial);""")
    connection.commit()
    print("Таблица users успешно создана!")
except (Exception, psycopg2.Error) as e:
    print("Не удалось создать таблицу users в БД\nВозможно она уже была создана ранее\nОшибка:", e)


@bot.message_handler(commands=["start"])
def start(message: Message):
    bot.send_message(message.from_user.id, "Добавляю id вашего аккаунта в базу данных...\nПожалуйста, подождите!!!")

    try:
        cursor.execute(f"insert into users (user_id) values ({message.from_user.id});")
        connection.commit()
    except psycopg2.Error as e:
        bot.send_message(message.from_user.id, "Ошибка на сервере!!! Не удалось добавить id вашего аккаунта в базу данных(\nПожалуйста, попробуйте позже")
        print("Не удалось добавить id аккаунта в БД(")
    else:
        bot.send_message(message.from_user.id, "Всё прошло успешно) Я запомнил вас. Ждите сигналов")
        print("id аккаунта добавлен в БД")


bot.polling(none_stop=True, interval=0)
