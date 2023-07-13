import logging
import re
import time
import urllib.request

import requests
from selenium.webdriver.common.by import By
from seleniumwire import webdriver
from seleniumwire.webdriver import FirefoxOptions

logger = logging.getLogger(__name__)
log_file_handler = logging.FileHandler('mainlog.log', 'a', 'utf-8')
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s')

log_file_handler.setFormatter(log_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(log_file_handler)


def search_mov(driver, name):
    logger.info('Searching movie: ' + str(name))
    search_input = driver.find_element(By.CLASS_NAME, 'b-search__field')
    search_input.send_keys(name)

    search_button = driver.find_element(By.CLASS_NAME, 'b-search__submit')
    search_button.click()
    time.sleep(1.2)

    movies = driver.find_elements(By.CLASS_NAME, 'b-content__inline_item')
    movies_arr = []
    i = 1
    for movie in movies:
        if i > 10:
            break

        mov = [movie.text.split('\n')]
        href = movie.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

        mov.append(href)
        movies_arr.append(mov)

        img_tag = movie.find_element(By.CSS_SELECTOR, 'img')
        urllib.request.urlretrieve(img_tag.get_attribute('src'), str(i) + '.jpg')

        i += 1

    # print(movies_arr)
    return movies_arr


def download_mov(driver, url, limit):
    logger.info('Started downloading movie to server url:{}'.format(url))

    driver.get(url)
    time.sleep(2.0)

    settings_button = driver.find_element(
        By.CSS_SELECTOR,
        '#oframecdnplayer > pjsdiv:nth-child(17) > pjsdiv:nth-child(3)'
    )
    settings_button.click()
    time.sleep(1.0)

    resolution_button = driver.find_element(
        By.CSS_SELECTOR,
        '#cdnplayer_settings > pjsdiv:nth-child(1) > pjsdiv:nth-child(1)'
    )
    resolution_button.click()
    time.sleep(1.0)

    # 0 is word resolution, resolutions start from id 1
    resolutions = driver.find_elements(By.XPATH, '//*[@f2id]')
    resolutions[1].click()
    time.sleep(1.5)

    # get video url from last request
    url_mov = ''
    for request in driver.requests:
        if request.response is not None and request.response.status_code == 302:
            logger.info("Request 302:" + str(request))
            url_mov = request.url
    # url with .mp4 in end
    url_mov = re.match(".*(.mp4)", url_mov).group(0)

    size_movie = requests.get(url_mov, stream=True).headers['Content-length']
    if int(size_movie) > limit:
        raise RuntimeError('Limit size of movie')

    start_download = time.time()
    urllib.request.urlretrieve(url_mov, 'mov.mp4')
    end_download = time.time()
    downloading_time = end_download - start_download

    logger.info('Downloading time of {}:{}'.format(url, downloading_time))
    return downloading_time


def init_driver():
    options_fire = FirefoxOptions()
    # options_fire.add_argument('-headless')
    options_fire.add_argument('--blink-settings=imagesEnabled=false')

    driver = webdriver.Firefox(options=options_fire)
    driver.get('https://hdrezka.tv/')
    return driver
