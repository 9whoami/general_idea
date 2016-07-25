#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from antigate import AntiGateError
from grab.error import GrabTimeoutError
from fake_useragent import UserAgent
from time import sleep
from random import shuffle, randint
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.keys import Keys

from browser import WebDriver
from captha_lib import RecognizeCaptcha
from config import Conf
from logger import Logger, call_info, get_class_variable_state
from threadpool import ThreadPool

__author__ = "whoami"
__version__ = "1.0.2"
__date__ = "09.07.16 17:56"
__description__ = """"""


class SearchInGoogle:
    search_result = None
    target_site = None

    @call_info
    def __init__(self, driver):
        try:
            self.driver = driver
            self.page_cnt = 0
            self.site_cnt = 0
            self.gen_result_limit()
            self.page_limit = randint(
                int(config.page_limit.split(',')[0]),
                int(config.page_limit.split(',')[1]))
            self.driver.get('https://www.google.com')
        except Exception as e:
            logger.error('It rases an exception with message: {!r}'.format(str(e)))

    @get_class_variable_state
    def __str__(self):
        pass

    @call_info
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

    @call_info
    def gen_result_limit(self):
        self.site_cnt = 0
        self.result_limit = randint(
            int(config.site_limit.split(',')[0]),
            int(config.site_limit.split(',')[1]))
        logger.info(self)

    @call_info
    def search(self, search_request):
        # self.driver.filling_web_element(".//*[@id='lst-ib']", search_request)
        # sleep(1)
        # self.driver.find_element_by_css_selector("body").send_keys(Keys.RETURN)

        input_field = self.driver.get_element_or_none(".//*[@id='lst-ib']")
        self.driver.filling_web_element(input_field, search_request)
        sleep(2)
        input_field.submit()

    @call_info
    def collect_result(self):
        search_results = ".//*[@id='rso']/.//div[@class='rc']/h3[@class='r']/a"
        self.search_result = self.driver.get_elements_by_xpath(search_results)
        for web_elem in self.search_result:
            href = self.driver.get_element_info(web_elem, 'href')
            if config.target_domain in href:
                self.target_site = web_elem
                break
        logger.info(self)

    @call_info
    def go_rand_result(self):
        while True:
            logger.info(self)
            try:
                if self.site_cnt >= self.result_limit:
                    raise IndexError
                else:
                    self.site_cnt += 1

                search_lnk = self.search_result.pop(randint(0, len(self.search_result)-1))
            except (IndexError, ValueError):
                if self.target_site:
                    self.search_result.clear()
                    self.search_result.append(self.target_site)
                    self.site_cnt -= 1
                    self.target_site = None
                    continue
                elif not self.go_to_next_page():
                    raise StopIteration
                else:
                    sleep(5)
                    self.collect_result()
                    continue

            href = self.driver.get_element_info(search_lnk, 'href')

            try:
                self.driver.open_link_in_new_tab(search_lnk)
            except (StaleElementReferenceException, WebDriverException) as e:
                print(e)
                continue
            yield href

    @call_info
    def go_to_next_page(self):
        if self.page_cnt >= self.page_limit:
            return False
        else:
            self.page_cnt += 1

        self.gen_result_limit()
        next_page = ".//*[@id='pnnext']"
        next_btn = self.driver.get_element_or_none(next_page)
        logger.info(self)
        return self.driver.btn_click(next_btn)


class ViewSite:
    @call_info
    def __init__(self, driver):
        self.driver = driver

    @get_class_variable_state
    def __str__(self):
        pass

    @call_info
    def scroll_down(self):
        timer(randint(
            int(config.freeze_time.split(',')[0]),
            int(config.freeze_time.split(',')[1])))
        while th_pool.is_alive():
            sleep(randint(1, 2))
            self.driver.scroll_down(500)

    @call_info
    def close(self):
        self.driver.close_current_tab()


class ViewTargetSite:
    @call_info
    def __init__(self, driver):
        self.driver = driver
        self.depth_max = randint(
            int(config.depth.split(',')[0]),
            int(config.depth.split(',')[1]))
        self.depth_cur = 0

    @get_class_variable_state
    def __str__(self):
        pass

    @call_info
    def scroll_down(self):
        timer(randint(
            int(config.freeze_time.split(',')[0]),
            int(config.freeze_time.split(',')[1])))

        while th_pool.is_alive():
            sleep(randint(1, 2))
            self.driver.scroll_down(500)

    @call_info
    def collect_lnk(self):
        self.links = self.driver.get_elements_by_xpath("//*[@href]")

    @call_info
    def go_to_rnd_lnk(self):
        while True:
            logger.info(self)
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

    @call_info
    def close(self):
        self.driver.close_current_tab()


def read_search_requests():
    logger.info('Reading search requests list...')

    try:
        with open('search_requests', 'r') as f:
            search_requests = f.read().split('\n')
        shuffle(search_requests)
    except Exception as e:
        logger.error('It raises an exception with message: {!r}'.format(str(e)))
        raise SystemExit
    else:
        logger.info('Reading search requests list...OK')

    return search_requests

logger = Logger()
logger.info("Initialization...")
try:
    fake_ua = UserAgent()
    th_pool = ThreadPool(max_threads=1)
    config = Conf()
    config.read_section('base')
    driver = None

    logger.info('Reading proxy list...')
    try:
        with open('proxy', 'r') as f:
            proxy_list = f.read().split('\n')
    except Exception as e:
        logger.error('It raises an exception with message: {!r}'.format(str(e)))
        raise SystemExit
    else:
        logger.info('Reading proxy list...OK')

    search_requests = read_search_requests()
except BaseException as e:
    logger.critical('Initialization raises an exception with message: {!r}'.format(str(e)))
    raise SystemExit
else:
    logger.info('Initialization...OK')


@th_pool.thread
def timer(seconds):
    logger.info('Sleep {} seconds'.format(seconds))
    for _ in range(0, seconds):
        sleep(1)

while True:
    try:
        try:
            logger.info('Receiving a search request...')
            request = search_requests.pop()
        except IndexError:
            logger.info('Request list is empty')
            search_requests = read_search_requests()
            continue
        else:
            logger.info('Receiving a search request...OK')

        while True:
            proxy = None
            # try:
            #     logger.info('Receiving a proxy...')
            #     proxy = proxy_list.pop()
            #     if proxy == '':
            #         raise IndexError
            # except IndexError:
            #     logger.error('Proxy list is empty...')
            #     raise SystemExit
            # else:
            #     logger.info('Receiving a proxy...OK')

            logger.info('Starting the Web driver...')
            try:
                driver = WebDriver(user_agent=fake_ua.random, proxy=proxy, proxy_type=config.proxy_type)
            except Exception as e:
                logger.error('Starting the Web driver raises an exception with a message: {!r}'.format(str(e)))
                continue
            else:
                logger.info('Starting the Web driver...OK')
                break

        sig = SearchInGoogle(driver)
        try:
            if not sig.captcha():
                raise AttributeError
            sig.search(request)
        except AttributeError:
            driver.close()
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

        logger.info('The work is finished, close the Web Driver')
        driver.close()
    except KeyboardInterrupt:
        logger.info('Job canceled by the user')
        raise SystemExit
