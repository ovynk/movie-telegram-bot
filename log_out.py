import telebot

bot = telebot.TeleBot('')

logout = bot.log_out()
print(logout)
