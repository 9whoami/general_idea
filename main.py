#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from antigate import AntiGateError
from grab.error import GrabTimeoutError
from random import shuffle
from fake_useragent import UserAgent
from time import sleep
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.keys import Keys

from random import randint
from browser import WebDriver
from logger import Logger
from config import Conf
from threadpool import ThreadPool
from captha_lib import RecognizeCaptcha

__author__ = "whoami"
__version__ = "0.0.1"
__date__ = "09.07.16 17:56"
__description__ = """"""


class SearchInGoogle:
    search_result = None

    def __init__(self, driver):
        self.driver = driver
        self.page_cnt = 0
        self.site_cnt = 0
        self.gen_result_limit()
        self.page_limit = randint(
            int(config.page_limit.split(',')[0]),
            int(config.page_limit.split(',')[1]))
        self.driver.get('https://www.google.com')

    def captcha(self):
        captcha_img = 'html/body/div/img'
        captcha_input = ".//*[@id='captcha']"

        img = self.driver.get_element_or_none(xpath=captcha_img)
        if img:
            antigate = RecognizeCaptcha()
            try:
                antigate.recognize(self.driver.take_screenshot(), img.rect)
            except (AntiGateError, GrabTimeoutError) as e:
                print(e)
                return False
            if antigate.captcha_result:
                self.driver.filling_web_element(captcha_input, antigate.captcha_result)
                self.driver.btn_click("html/body/div/form/input[5]")
                sleep(2)
                return self.captcha()
            else:
                return False
        else:
            return True

    def gen_result_limit(self):
        self.site_cnt = 0
        self.result_limit = randint(
            int(config.site_limit.split(',')[0]),
            int(config.site_limit.split(',')[1]))

    def search(self, search_request):
        self.driver.filling_web_element(".//*[@id='lst-ib']", search_request)
        sleep(1)
        self.driver.find_element_by_css_selector("body").send_keys(Keys.RETURN)
        input_field = self.driver.get_element_or_none(".//*[@id='lst-ib']")
        self.driver.filling_web_element(input_field, search_request)
        input_field.submit()

    def collect_result(self):
        search_results = ".//*[@id='rso']/.//div[@class='rc']/h3[@class='r']/a"
        self.search_result = self.driver.get_elements_by_xpath(search_results)

    def go_rand_result(self):
        while True:
            try:
                if self.site_cnt >= self.result_limit:
                    raise IndexError
                else:
                    self.site_cnt += 1

                search_lnk = self.search_result.pop(randint(0, len(self.search_result)-1))
            except (IndexError, ValueError):
                if not self.go_to_next_page():
                    raise StopIteration
                self.collect_result()
                search_lnk = self.search_result.pop(randint(0, len(self.search_result) - 1))

            href = self.driver.get_element_info(search_lnk, 'href')

            try:
                self.driver.open_link_in_new_tab(search_lnk)
            except (StaleElementReferenceException, WebDriverException) as e:
                print(e)
                continue
            yield href

    def go_to_next_page(self):
        if self.page_cnt >= self.page_limit:
            return False
        else:
            self.page_cnt += 1

        self.gen_result_limit()
        next_page = ".//*[@id='pnnext']"
        next_btn = self.driver.get_element_or_none(next_page)
        return self.driver.btn_click(next_btn)


class ViewSite:
    def __init__(self, driver):
        self.driver = driver

    def scroll_down(self):
        timer(randint(
            int(config.freeze_time.split(',')[0]),
            int(config.freeze_time.split(',')[1])))
        while th_pool.is_alive():
            sleep(randint(1, 2))
            self.driver.scroll_down(500)

    def close(self):
        self.driver.close_current_tab()


class ViewTargetSite:
    def __init__(self, driver):
        self.driver = driver
        self.depth_max = randint(
            int(config.depth.split(',')[0]),
            int(config.depth.split(',')[1]))
        self.depth_cur = 0

    def scroll_down(self):
        timer(randint(
            int(config.freeze_time.split(',')[0]),
            int(config.freeze_time.split(',')[1])))

        while th_pool.is_alive():
            sleep(randint(1, 2))
            self.driver.scroll_down(500)

    def collect_lnk(self):
        self.links = self.driver.get_elements_by_xpath("//*[@href]")

    def go_to_rnd_lnk(self):
        while True:
            self.collect_lnk()
            try:
                if self.depth_cur >= self.depth_max:
                    raise StopIteration

                link = self.links.pop(randint(0, len(self.links)-1))
            except (IndexError, ValueError):
                raise StopIteration
            href = self.driver.get_element_info(link, 'href')
            if config.target_domain not in href:
                continue
            driver.execute_script('arguments[0].setAttribute("target","");', link)
            if not self.driver.btn_click(link):
                continue
            self.depth_cur += 1
            yield

    def close(self):
        self.driver.close_current_tab()


fake_ua = UserAgent()
th_pool = ThreadPool(max_threads=1)
config = Conf()
config.read_section('base')
driver = None


@th_pool.thread
def timer(seconds):
    for _ in range(0, seconds):
        sleep(1)

with open('proxy', 'r') as f:
    proxy_list = f.read().split('\n')


def read_search_requests():
    with open('search_requests', 'r') as f:
        search_requests = f.read().split('\n')
    shuffle(search_requests)
    return search_requests

search_requests = read_search_requests()

while True:
    try:
        request = search_requests.pop()
    except IndexError:
        search_requests = read_search_requests()
        continue

    while True:
        # proxy = None
        try:
            proxy = proxy_list.pop()
            if proxy == '':
                raise IndexError
        except IndexError:
            Logger().error('Закончились прокси')
            raise SystemExit

        try:
            driver = WebDriver(user_agent=fake_ua.random, proxy=proxy, proxy_type=config.proxy_type)
        except Exception as e:
            print(e)
            driver.close()
            continue
        else:
            break

    # driver = WebDriver(user_agent=fake_ua.random)

    sig = SearchInGoogle(driver)
    if not sig.captcha():
        driver.close()
        continue
    try:
        sig.search(request)
    except AttributeError:
        continue
    sleep(2)
    sig.collect_result()

    for url in sig.go_rand_result():
        if config.target_domain in url:
            vts = ViewTargetSite(driver)
            vts.scroll_down()
            for _ in vts.go_to_rnd_lnk():
                vts.scroll_down()
            vts.close()
            break
        else:
            vs = ViewSite(driver)
            vs.scroll_down()
            vs.close()

    driver.close()
