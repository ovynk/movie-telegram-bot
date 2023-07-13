import logging
from contextlib import ExitStack
from functools import wraps

from moviepy.editor import *
from telebot import types, apihelper, TeleBot

import scrape_rezka
import split_video

apihelper.MAX_RETRIES = 100000
apihelper.API_URL = "http://localhost:8081/bot{0}/{1}"
apihelper.READ_TIMEOUT = 3661
apihelper.CONNECT_TIMEOUT = 3662

bot = TeleBot('')
ALLOWED_IDS = []
driver = scrape_rezka.init_driver()
movies_arr = []


# to restrict access for everyone who is not in ALLOWED_IDS
def private_access(f):
    @wraps(f)
    def f_restrict(message, *args, **kwargs):
        user = message.from_user

        if user.id in ALLOWED_IDS:
            return f(message, *args, **kwargs)
        else:
            lang_code = None
            username = None
            try:
                lang_code = user.lang_code
                username = user.username
            except AttributeError:
                logger.info('Attribute error when check access')

            logger.info('Private access function: restricted to user: {}, id: {}, lang_code: {}'
                        .format(username, user.id, lang_code))
            bot.reply_to(message, text='Sorry, you have not received permission in this bot')

    return f_restrict


@bot.message_handler(commands=['start'])
@private_access
def start(message):
    bot.send_message(message.chat.id, 'Ищи фильм по названию')
    logger.info('Start command used')


@bot.message_handler()
@private_access
def get_name_mov(message: types.Message):
    global movies_arr
    movies_arr = scrape_rezka.search_mov(driver, message.text)
    media_group = []
    photos = []
    text_all = ''
    markup_inline = types.InlineKeyboardMarkup()

    for i in range(len(movies_arr)):
        photo = open(str(i + 1) + '.jpg', 'rb')
        photos.append(photo)
        media_group.append(types.InputMediaPhoto(photo))

        description_mov = movies_arr[i][0]
        text_all += str(i + 1) + '. ' + ' '.join(description_mov) + '\n\n'

        button = types.InlineKeyboardButton(text=str(i + 1) + '.' + description_mov[1],
                                            callback_data=str(i))
        markup_inline.add(button)

    bot.send_media_group(message.chat.id, media=media_group)
    bot.send_message(message.chat.id, text_all, reply_markup=markup_inline)

    for f in photos:
        f.close()
    for f in os.listdir():
        if f.endswith(".jpg"):
            os.remove(f)


@bot.callback_query_handler(func=lambda call: True)
@private_access
def callback_select_mov(call):
    try:
        movie_name = movies_arr[int(call.data)][0][1]
        description = ' '.join(movies_arr[int(call.data)][0])
        url_call = movies_arr[int(call.data)][1]
        movie_file = "mov.mp4"

        bot.send_message(call.message.chat.id,
                         "'{}' будет отправлен в течении 10-20 минут, ждите.".format(movie_name))

        try:
            download_time = scrape_rezka.download_mov(driver, url_call, 10_400_000_000)
        except RuntimeError as re:
            bot.send_message(call.message.chat.id,
                             "К сожалению фильм больше 10ГБ невозможно отправить из-за ограничений сервера")
            logger.error("Stop downloading. Video size is more than 10GB")
            return

        logger.info("Start splitting video with url '{}' in cuts".format(url_call))
        cuts = split_video.split_via_size(movie_file)

        logger.info("Start sending video with url '{}' or cuts".format(url_call))
        send_group_video(
            chat_id=call.message.chat.id,
            videos=movie_file if not cuts else cuts,
            text=description
        )
    except IndexError as ie:
        bot.send_message(call.message.chat.id, "Извините, кнопка не работает, используйте поиск")
        logger.warning("Invalid index in buttons")
    except OSError as oe:
        bot.send_message(call.message.chat.id, "Извините, возникла ошибка во время отправки видео")
        logger.warning("OSError in callback_select_mov")
    finally:
        os.system("taskkill /im ffmpeg-win64-v4.2.2.exe /t /f")
        driver.requests.clear()
        driver.delete_all_cookies()
        for f in os.listdir():
            if f.endswith(".mp4"):
                os.remove(f)


@bot.message_handler(commands=['driver_quit'])
@private_access
def start(message):
    driver.quit()
    logger.info('Quit driver')


@bot.message_handler(commands=['driver_restart'])
@private_access
def start(message):
    logger.info('Restart driver')
    global driver
    driver.quit()
    driver = scrape_rezka.init_driver()


def send_group_video(chat_id, videos, text):
    if type(videos) is list:
        media_group = []

        if len(videos) > 2:
            for i in range(len(videos)):
                with open(videos[i], 'rb') as video:
                    clip = VideoFileClip(videos[i])
                    bot.send_video(chat_id=chat_id,
                                   video=video,
                                   duration=int(clip.duration),
                                   width=clip.size[0],
                                   height=clip.size[1],
                                   supports_streaming=True,
                                   caption=text + '\n{} из {} частей видео'.format(i + 1, len(videos)))
        else:
            with ExitStack() as stack:
                files = [stack.enter_context(open(f_name, 'rb')) for f_name in videos]
                for i in range(len(videos)):
                    clip = VideoFileClip(videos[i])
                    media_group.append(
                        types.InputMediaVideo(
                            files[i],
                            duration=int(clip.duration),
                            width=clip.size[0],
                            height=clip.size[1],
                            supports_streaming=True,
                            caption=text if i == len(videos) - 1 else ''
                        )
                    )
                bot.send_media_group(chat_id=chat_id, media=media_group)  # , timeout=1320)
    else:
        with open(videos, 'rb') as video:
            clip = VideoFileClip(videos)
            bot.send_video(chat_id=chat_id,
                           video=video,
                           duration=clip.duration,
                           width=clip.size[0],
                           height=clip.size[1],
                           supports_streaming=True,
                           caption=text)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    log_file_handler = logging.FileHandler('mainlog.log', 'a', 'utf-8')
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s')

    log_file_handler.setFormatter(log_formatter)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(log_file_handler)

    while True:
        try:
            print('Try start bot!!!')
            bot.polling(non_stop=True)
        except Exception as e:
            print('Exception:' + str(e))
            logger.error('Exception:' + str(e))
