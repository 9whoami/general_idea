# -*- coding: utf-8 -*-
from PIL import Image
from antigate import AntiGate
from logger import Logger
from config import Conf

__author__ = 'whoami'
__version__ = '0.0.0'
__date__ = '30.03.16 3:38'
__description__ = """
Description for the python module
"""
logger = Logger()


class RecognizeCaptcha(AntiGate):
    captcha_file = 'captcha.png'

    def __init__(self):
        self.conf = Conf()
        self.conf.read_section('antigate')
        super().__init__(auto_run=False, **self.conf.namespace)

    def crop_image(self, image_name, captcha_size):
        self.conf.read_section('webdriver')
        image = Image.open(self.conf.screen_dir + image_name)
        image.crop(captcha_size).save(self.captcha_file)

    def _balance(self):
        balanse = super().balance()
        logger.info("Баланс антикаптчи: {}".format(balanse))
        if balanse < 1:
            raise RuntimeWarning('Пополните баланс сервиса антикапчи')

    def recognize(self, image: str, rect: 'element rect'):
        try:
            self.balance()
        except RuntimeWarning:
            return None

        captcha_size = (rect['x'],
                        rect['y'],
                        rect['width'] + rect['x'] - 1,
                        rect['height'] + rect['y'] - 1)

        self.crop_image(image, captcha_size)
        super().run(self.captcha_file)

