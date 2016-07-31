#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from os import path
from datetime import datetime
from antigate import AntiGateError
from grab import Grab
from grab.error import GrabTimeoutError
from fake_useragent import UserAgent
from time import sleep
from random import shuffle, randint
from selenium.common.exceptions import StaleElementReferenceException, WebDriverException

from virtual_display import VirtualDisplay
from browser import WebDriver
from captha_lib import RecognizeCaptcha
from config import Conf
from logger import Logger, call_info, get_class_variable_state
from threadpool import ThreadPool

__author__ = "whoami"
__version__ = "1.0.2"
__date__ = "09.07.16 17:56"
__description__ = """"""


class Statistic:
    JUMP_TO_GENERAL_SITE='jump_to_general_site'
    JUMP_TO_OTHER_SITE='jump_to_other_site'
    SEARCH_KEYWORD='search_keyword'

    @call_info
    def __init__(self, general_site_list: iter, keywords: iter):
        self._start_time = datetime.now()
        self.full_time = dict(
            start_time=str(self._start_time),
            search_keyword={key:0 for key in keywords},
            jump_to_general_site={key:0 for key in general_site_list},
            jump_to_other_site=0
        )

        self.update_today(general_site_list, keywords)
        self.session_id, self.stat_file = self._make_stat_file()

    @call_info
    def _make_stat_file(self):
        def gen_session_id():
            return '{}{}{}-{}{}{}-{}{}{}'.format(*[randint(0,9) for i in range(100)])
        session_id = gen_session_id()
        file_ext = '.txt'
        while path.exists(session_id + file_ext):
            session_id = gen_session_id()

        stat_file = session_id + file_ext
        return session_id, stat_file

    @call_info
    def update_today(self, general_site_list: iter, keywords: iter):
        self.today = dict(
            search_keyword={key: 0 for key in keywords},
            jump_to_general_site={key: 0 for key in general_site_list},
            jump_to_other_site=0
        )

    def __str__(self):
        return '\nsession_id: {}\nfull_time: {}\ntoday: {}'.format(
            self.session_id, self.full_time, self.today)

    @call_info
    def store(self):
        with open(self.stat_file, 'w') as f:
            f.write(self.__str__())

    @call_info
    def inc(self, key1, key2=None):
        if key2:
            self.full_time[key1][key2] += 1
            self.today[key1][key2] += 1
        else:
            self.full_time[key1] += 1
            self.today[key1] += 1

    @call_info
    def check_update(self):
        cur_date = datetime.now()
        logger.info(cur_date, self._start_time)
        difference = cur_date - self._start_time
        return bool(difference.days) is True



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
        redirect = 1
        while True:
            logger.info(self)
            if redirect:
                self.collect_lnk()
                redirect = False
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
            redirect = self.driver.btn_click(link)
            if not redirect:
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
        raise Exception
    else:
        logger.info('Reading search requests list...OK')

    return search_requests


def check_url(target_domains: iter, url: str) -> bool:
    check_url.last_index = -1
    for domain in target_domains:
        if domain in url:
            check_url.last_index = target_domains.index(domain)
            return True


def get_proxy():
    logger.info('Reading proxy list...')
    proxy = list()
    try:
        with open('proxy', 'r') as f:
            file_text = f.read()
            if file_text:
                proxy = file_text.split('\n')
            else:
                raise Exception('Proxy file is empty!')
        if proxy[0].startswith('http'):
            g = Grab()
            g.go(proxy[0])
            if g.response.code == 200:
                response = str(g.response.body, encoding='cp1251')
                proxy = response.split('\n')
    except Exception as e:
        logger.error('It raises an exception with message: {!r}'.format(str(e)))
        raise Exception(e)
    else:
        logger.info('Reading proxy list...OK')
        return proxy


def proxy_update(proxy_old):
    proxy_old = set(proxy_old)
    proxy = get_proxy()
    if isinstance(proxy, list):
        proxy = set(proxy)
        proxy = list(proxy.difference(proxy_old))
    return proxy


def runer():
    global logger, proxy_list, search_requests, proxy
    logger = Logger()
    logger.info("Initialization...")
    try:
        fake_ua = UserAgent()
        config = Conf()
        config.read_section('base')
        target_sites = config.target_domain.split(',')
        driver = None
        proxy_list = get_proxy()
        proxy_list_old = list()
        search_requests = read_search_requests()
        statistics = Statistic(general_site_list=target_sites, keywords=search_requests)
    except BaseException as e:
        logger.critical('Initialization raises an exception with message: {!r}'.format(str(e)))
        raise Exception
    else:
        logger.info('Initialization...OK')


    try:
        logger.info(statistics)
        if statistics.check_update():
            statistics.update_today(general_site_list=target_sites, keywords=search_requests)
        statistics.store()

        try:
            logger.info('Receiving a search request...')
            request = search_requests.pop()
            statistics.inc(statistics.SEARCH_KEYWORD, request)
        except IndexError:
            logger.info('Request list is empty')
            search_requests = read_search_requests()
            return
        else:
            logger.info('Receiving a search request...OK')

        attempt = 0
        attempts = 10
        while True:
            if attempt >= attempts:
                raise Exception('You have exceeded the number of attempts to start web driver')
            proxy_list = proxy_update(proxy_list_old[:])
            proxy = None
            try:
                logger.info('Receiving a proxy...')
                proxy = proxy_list.pop()
            except IndexError:
                logger.error('Proxy list is empty...')
                proxy_list = get_proxy()
                attempt += 1
                continue
            else:
                proxy_list_old.append(proxy)
                logger.info('Receiving a proxy...OK')

            logger.info('Starting the Web driver...')
            try:
                driver = WebDriver(user_agent=fake_ua.random, proxy=proxy, proxy_type=config.proxy_type)
            except Exception as e:
                logger.error('Starting the Web driver raises an exception with a message: {!r}'.format(str(e)))
                attempt += 1
                continue
            else:
                logger.info('Starting the Web driver...OK')
                break

        sig = SearchInGoogle(driver)
        try:
            assert sig.captcha()
            sig.search(request)
            assert sig.captcha()
        except (AttributeError, AssertionError):
            driver.close()

        sleep(2)

        sig.collect_result()

        for url in sig.go_rand_result():
            if check_url(target_domains=target_sites, url=url):
                vts = ViewTargetSite(driver)
                vts.scroll_down()
                for _ in vts.go_to_rnd_lnk():
                    vts.scroll_down()
                vts.close()
                statistics.inc(statistics.JUMP_TO_GENERAL_SITE, target_sites[check_url.last_index])
                break
            else:
                vs = ViewSite(driver)
                vs.scroll_down()
                vs.close()
                statistics.inc(statistics.JUMP_TO_OTHER_SITE)

        logger.info('The work is finished, close the Web Driver')
        driver.close()
    finally:
        statistics.store()


th_pool = ThreadPool(max_threads=1)


@th_pool.thread
def timer(seconds):
    logger.info('Sleep {} seconds'.format(seconds))
    for _ in range(0, seconds):
        sleep(1)

