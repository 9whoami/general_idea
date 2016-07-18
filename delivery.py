# -*- coding: utf-8 -*-
import settings as config
from imports.logger import Logger
from imports.captha_lib import RecognizeCaptcha
from imports.exceptions import BaseError
from imports.exceptions import SendMessageError

__author__ = 'whoami'
__version__ = '0.0.0'
__date__ = '27.03.16 0:55'
__description__ = """
Рассылка сообщений селлерам
"""


class Delivery:
    def __init__(self, browser: "selenium.webdriver instance"):
        self.browser = browser
        self.subject = None
        self.message = None
        self.attempt = 4
        self.logger = Logger()

        self.x_contact_seller = config.items_xpath['contact_lnk']
        self.x_switch_topic = config.items_xpath['topic']
        self.x_contact_btn = config.items_xpath['contact_btn']

        self.x_subject = config.contact_xpath['topic']
        self.x_message = config.contact_xpath['msg']
        self.x_captcha_edit = config.contact_xpath['captha_edit']
        self.x_send_message = config.contact_xpath['send_btn']

        self.x_subject_error = config.contact_xpath['topic_error']
        self.x_message_error = config.contact_xpath['msg_error']
        self.x_captcha_error = config.contact_xpath['captcha_error']

        self.x_success = config.contact_xpath['success']
        self.x_denied = config.contact_xpath['denied']

        self.x_seller_name = config.items_xpath['seller_name']

    def run(self, items):
        self.logger.info('Запускаем рассылку')
        self.message_preload()
        for item in items:
            self.browser.get(item)

            try:
                self.filter()
                self.redirect_to_contact()
                self.prepare_post_message()
            except AssertionError:
                self.logger.info('Ой, что то пошло не так')
                continue

            for cnt in range(self.attempt):
                self.logger.info(
                    '{}-ая попытка отправить сообщение'.format(cnt))
                try:
                    self.message_post()
                    self.conflict_resolution()
                except BaseError as e:
                    self.logger.error(e)
                    self.browser.refresh()
                    continue
                except AssertionError:
                    break

    def filter(self):
        try:
            seller_name = self.browser.get_text_from_element(self.x_seller_name)
        except Exception:
            raise AssertionError

        with open(config.seller_cache, 'r') as f:
            seller_cache = f.read().split('\n')

        if seller_name in seller_cache:
            self.logger.info(
                'Продавцу {} уже отправляли сообщение'.format(seller_name))
            raise AssertionError
        else:
            self.logger.info(
                'Отправляем сообщение продавцу {}'.format(seller_name))
            seller_cache.append(seller_name)
            with open(config.seller_cache, 'a') as f:
                f.write(seller_name)

    def redirect_to_contact(self):
        self.logger.info('Пытаемся найти ссылку для обратной связи')
        element = self.browser.get_element_or_none(self.x_contact_seller)
        if element is None:
            self.logger.warning('Не найдена ссылка для обратной связи')
            assert False
        self.browser.get(self.browser.get_element_info(element, 'href'))

    def prepare_post_message(self):
        self.logger.info('Пытаемся перейти на страницу отправки сообщения')
        assert self.browser.btn_click(self.x_switch_topic)
        assert self.browser.btn_click(self.x_contact_btn)
        what_this = self.browser.get_text_from_element(self.x_success)
        if what_this:
            self.logger.warning(what_this)
            assert False

    def message_post(self):
        self.logger.info('Пытаемся отправить сообщение')
        assert self.browser.filling_web_element(self.x_subject, self.subject)
        assert self.browser.filling_web_element(self.x_message, self.message)
        assert self.recognize_captcha()
        assert self.browser.btn_click(self.x_send_message)

    def recognize_captcha(self):
        if not self.browser.get_element_or_none(self.x_captcha_edit):
            self.logger.warning('Не найдено поле для ввода капчи')
            return True
        self.logger.info('Начинаю расшифровку капчи')

        scr_name = self.browser.take_screenshot()

        recaptcha = RecognizeCaptcha()
        recaptcha.recognize(scr_name, config.delivery_captcha_size)
        if recaptcha.captcha_result:
            self.logger.info(
                'Получен ответ: {}'.format(recaptcha.captcha_result))
            return self.browser.filling_web_element(self.x_captcha_edit,
                                                    recaptcha.captcha_result)
        else:
            self.logger.error('Не удалось получить ответ...')
            return False

    def conflict_resolution(self):
        self.logger.info('Приступаю к поиску и разрешению конфликтов')
        err_text = list()
        err_text.append(
            self.browser.get_text_from_element(self.x_subject_error))
        err_text.append(
            self.browser.get_text_from_element(self.x_message_error))
        err_text.append(
            self.browser.get_text_from_element(self.x_captcha_error))

        success = self.browser.get_text_from_element(self.x_success)
        denied = self.browser.get_text_from_element(self.x_denied)

        for error in err_text:
            if error:
                raise SendMessageError(error)

        if success:
            self.logger.info(success)
            raise AssertionError

        if denied:
            self.logger.error(denied)

            if config.limit_partial_text in denied:
                raise SystemExit()
            else:
                raise AssertionError

    def message_preload(self):
        self.logger.info('Получение сообщения для рассылки')
        with open(config.message_file, 'r') as f:
            self.subject = f.readline()
            self.message = f.read()

