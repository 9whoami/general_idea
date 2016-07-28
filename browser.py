# -*- coding: utf-8 -*-

from datetime import datetime
from random import randint
from logger import Logger
from selenium.webdriver.common.keys import Keys
from virtual_display import VirtualDisplay
from config import Conf

from random import choice
from time import sleep
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.proxy import *
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

__author__ = 'whoami'
__version__ = '2.3.0'
__date__ = '27.03.16 0:46'
__description__ = """
Обертка для selenium.webdriver
"""

config = Conf()
config.read_section('webdriver')


class SwithSuperMetaclass(type):
    """
    Метакласс для подметы класса родителя для класса WebDriver.
    """

    def __new__(cls, name, bases, dct):
        if cls.web_driver_select():
            bases = webdriver.PhantomJS,
        else:
            bases = webdriver.Firefox,

        return type.__new__(cls, name, bases, dct)

    @staticmethod
    def web_driver_select():
        web_drivers = {config.phantomjs: 1, config.firefox: 0}
        try:
            return web_drivers[config.web_driver]
        except KeyError:
            raise SystemExit("Укажите правильный параметр web driver")


class WebDriver(metaclass=SwithSuperMetaclass):
    """
    Обертка для selenium.webdriver
    """

    _profile = None

    def __init__(self, **kwargs):
        self.logger = Logger()
        self.driver_profile = kwargs

        super().__init__(**self.driver_profile)

        self.set_window_size(self.heigth, self.width)
        config.load_timeout = int(config.load_timeout)
        self.set_page_load_timeout(config.load_timeout)
        config.implicitly_wait = int(config.implicitly_wait)
        self.implicitly_wait(config.implicitly_wait)
        self.get(config.test_url)

        self.scroll_method = randint(0,2)

    def __del__(self):
        try:
            self.take_screenshot()
        except Exception:
            pass

        try:
            self.quit()
        except Exception:
            pass

    @staticmethod
    def proxy_validation(proxy: str, ptype: str, web_site: str='https://whoer.net/') -> bool:
        """
        Проверка живучести прокси.
        :param proxy: IP:PORT прокси
        :param ptype: Тип прокси
        :param web_site: сайт который будет загружен для проверки соединения
        :return:
        """
        if proxy is None:
            return True

        try:
            from grab import Grab
            from grab import GrabError
        except ImportError:
            print('Для валидации прокси необходим Grab!')
            return True

        g = Grab()
        g.setup(proxy=proxy,
                proxy_type=ptype,
                connect_timeout=5,
                timeout=60)

        try:
            print('Начинаем проверку прокси url={!r}'.format(web_site))
            g.go(web_site)
        except GrabError:
            print('Прокси {!r} мертв'.format(proxy))
            return False
        else:
            print('Прокси {!r} жив'.format(proxy))
            return True

    @property
    def heigth(self):
        return int(choice(config.br_heigth.split(',')))

    @property
    def width(self):
        return int(choice(config.br_width.split(',')))

    @property
    def driver_profile(self):
        return self._profile

    @driver_profile.setter
    def driver_profile(self, kwargs):
        user_agent = kwargs.get('user_agent', None)
        proxy = kwargs.get('proxy', None)
        proxy_type = kwargs.get('proxy_type', None)

        try:
            if not self.proxy_validation(proxy=proxy, ptype=proxy_type):
                raise Exception('Proxy is down')

            if SwithSuperMetaclass.web_driver_select():
                dcap = dict(DesiredCapabilities.PHANTOMJS).copy()
                service_args = config.service_args if \
                    isinstance(config.service_args, list) else list()

                if proxy:
                    service_args.append('--proxy={}'.format(proxy))
                if proxy_type and proxy:
                    service_args.append('--proxy-type={}'.format(proxy_type))
                if user_agent:
                    dcap["phantomjs.page.settings.userAgent"] = user_agent

                self._profile = dict(desired_capabilities=dcap,
                                     service_args=service_args)
            else:
                ff_profile = webdriver.FirefoxProfile()
                if user_agent:
                    ff_profile.set_preference(
                        "general.useragent.override", user_agent)
                    ff_profile.set_preference(  # Remote DNS
                        "network.proxy.socks_remote_dns", True)
                    # media.peerconnection.enabled
                ff_profile.set_preference(  # Remote DNS
                    "media.peerconnection.enabled", False)

                if proxy:
                    proxy_ = Proxy(dict(proxyType=ProxyType.MANUAL,
                                       socksProxy=proxy))
                else:
                    proxy_ = None

                self._profile = dict(firefox_profile=ff_profile, proxy=proxy_)

        except Exception as e:
            self.logger.debug(e)
            raise SystemError()

        self.logger.info(
            "Запуск браузера {} с параметрами "
            "user_agent: {}, "
            "proxy: {}".format(config.web_driver, user_agent, proxy))

    def _get_element(self, locator_strategies, locator):
        """
        Ищет элемент на странице с неявным ожиданием его появления.
        Если в течение ожидания элемент не появился возвращается None
        :param locator_strategies:
        :param locator:
        :return:
        """
        config.explicit_waits = int(config.explicit_waits)
        try:
            element = WebDriverWait(self, config.explicit_waits).until(
                EC.presence_of_element_located((locator_strategies, locator)))
        except TimeoutException:
            element = None
        return element

    def get_element_or_none(self, xpath: 'str or WebElement'):
        """
        Получение элемента по xpath
        :param xpath:
        :return:
        """
        if isinstance(xpath, WebElement):
            return xpath
        element = self._get_element(By.XPATH, xpath)
        return element

    def find_element_by_partial_link(self, link_text):
        """
        Получение элементы по части названия.
        :param link_text:
        :return:
        """
        element = self._get_element(By.PARTIAL_LINK_TEXT, link_text)
        return element

    def take_screenshot(self):

        file_name = '{}.png'.format(str(datetime.now()))

        try:
            self.save_screenshot(config.screen_dir + file_name)

            self.logger.info(
                "Создан снимок окна браузера: {!r}".format(file_name))
        except Exception as e:
            self.logger.debug(e)
            return None

        return file_name

    def get(self, url):
        """
        Загрузка страницы с повторением при неудаче
        :param url:
        :return:
        """
        for i in range(0, 4):
            self.logger.info(
                '{!r}-ая попытка перехода по url: {!r}'.format(i + 1, url))

            try:
                self._get(url)
            except Exception:
                self.logger.warning('Не удалось загрузить страницу')
                continue
            else:
                self.logger.info('Страница загружена')
                return True

    def _get(self, url):
        is_not_load = lambda page_source: load_error in page_source or \
                                          blank_source in page_source
        load_error = '<!ENTITY loadError.label "Проблема при загрузке страницы">'
        blank_source = '<html><head></head><body></body></html>'

        super().get(url)

        result = self.page_source
        self.take_screenshot()

        if is_not_load(result):
            raise Exception('Некоректный HTML')

        return result

    def get_elements_by_xpath(self, xpath):
        """
        Получение списка элементов по xpath
        :param xpath:
        :return:
        """
        try:
            elements = self.find_elements_by_xpath(xpath)
        except Exception:
            elements = []
        return elements

    def get_element_info(self, web_element, attributes: 'list or str') -> list:
        web_element = self.get_element_or_none(web_element)
        if web_element is None: return None

        if isinstance(attributes, (list, tuple)):
            result = [web_element.get_attribute(attribute) for attribute in
                      attributes]
        elif isinstance(attributes, str):
            result = web_element.get_attribute(attributes)
        else:
            # result = None
            raise ValueError(
                "Expected 'list', 'tuple' or 'str' not {!r}".format(
                    attributes))

        return result

    def get_text_from_element(self, xpath: str) -> str:
        web_element = self.get_element_or_none(xpath)
        inner_text = web_element.text if web_element else None
        return inner_text

    def filling_web_element(self, xpath: str, value: str):
        web_element = self.get_element_or_none(xpath)
        if not web_element: return False

        try:
            try:
                web_element.clear()
            except Exception:
                pass
            web_element.send_keys(value)
            return True
        except Exception:
            return False

    def btn_click(self, xpath: str, freeze: int = 0,
                  screen: bool = True, **kwargs):
        if screen: self.take_screenshot()

        btn = self.get_element_or_none(xpath)
        if btn is None: return False

        try:
            btn.click()
            sleep(freeze)
            return True
        except Exception:
            return False

    def checkbox_checked(self, xpath: str, **kwargs):
        web_elem = self.get_element_or_none(xpath)
        if web_elem is None:
            return False

        checked = self.get_element_info(web_elem, 'checked')
        try:
            return True if checked else self.btn_click(xpath, screen=False)
        except Exception:
            return False

    def selection(self, xpath, value):
        element = self.get_element_or_none(xpath)
        if element is None:
            return False

        try:
            select = Select(element)
            try:
                select.select_by_value(value)
            except Exception:
                select.select_by_visible_text(value)
            return True
        except Exception:
            return False

    def text_contains(self, text):
        web_element = self.get_element_by_partial_text(text)
        return web_element.text if web_element else None

    def get_element_by_partial_text(self, text):
        return self.get_element_or_none(
            "//*[contains(text(),{!r})]".format(text))

    def load_stop(self):
        self.execute_script('window.stop();')

    def open_new_tab(self, url=None):
        self.find_element_by_css_selector("body").send_keys(Keys.CONTROL + "n")
        if url:
            self.get(url)

    def switch_next_tab(self):
        # self.find_element_by_css_selector("body").send_keys(Keys.CONTROL + Keys.TAB)
        self.switch_to_window(self.window_handles[1])
        self.switch_to_active_element()

    def swith_previous_tab(self):
        self.switch_to_window(self.window_handles[0])
        self.switch_to_active_element()

    def close_current_tab(self):
        # self.find_element_by_css_selector("body").send_keys(Keys.CONTROL + "w")
        self.close()
        self.swith_previous_tab()

    def open_link_in_new_tab(self, lnk_element):
        ActionChains(self).key_down(Keys.SHIFT).click(lnk_element).key_up(Keys.SHIFT).perform()
        self.switch_next_tab()
        sleep(config.load_timeout)

    def scroll_down(self, y):
        def js():
            self.execute_script("document.documentElement.scrollTop += {};".format(y))

        def arrow():
            self.find_element_by_css_selector("body").send_keys(Keys.ARROW_DOWN)

        def page_down():
            self.find_element_by_css_selector("body").send_keys(Keys.PAGE_DOWN)

        scroll_method = {0: js, 1: arrow, 2: page_down}

        try:
            scroll_method[self.scroll_method]()
        except Exception:
            return

    def scroll_up(self, y):
        try:
            self.execute_script("document.documentElement.scrollTop -= {};".format(y))
        except Exception:
            return
