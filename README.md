# movie-telegram-bot

Telegram bot that search and sends movies.
<br>
Libraries: Telebot, Selenium, moviepy

## Usage

To search video user has to send name of movie, cartoon or anime. Search works only in English, Ukrainian or Russian otherwise bot find nothing.
Bot scrapes movies from hdrezka.tv which is Ukrainian website. After finding results bot sends send the poster, name, genre, and date of 
movies as a massage with buttons. It’s made to make the user comfortable when choosing one for downloading.
When user touchs button with number and name of movie, bot starts to download it on server and after that sending from server to chat.
Telegram limits are 2GB, so video may be sent by parts by 1.5GB.

## Run

Also there are limits in Telegram API, so its not possible to send files which size is more than 50MB.
To solve this problem, there is opportunity to set up the bot in local server.

<a href="https://tdlib.github.io/telegram-bot-api/build.html">Here</a> is link for installing local server for your OS
<br>
All <a href="https://github.com/tdlib/telegram-bot-api">documentation</a>(necessary) about local server

1. You need to install it(~5GB) into your main folder with venv.
2. Then, you need to paste your bot token in `Telebot('')` in main.py 
3. Start local server for bot with your api-id and api-hash `./telegram-bot-api --api-id= --api-hash=`
4. And finally run main.py
