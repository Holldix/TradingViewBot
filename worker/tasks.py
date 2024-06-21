import telebot, os, sys, psycopg2
from dotenv import load_dotenv
load_dotenv()
from .celery import app


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


@app.task
def send_signal(coin, movement):
    cursor.execute("select user_id from users")

    users = cursor.fetchall()

    for user in users:
        bot.send_message(user[0], f"{movement}\n{coin}")
