import colorlog
import logging
import os

FORMAT = '%(log_color)s%(asctime)s [%(process)s] - %(name)-40s  %(levelname)s: %(message)s'
ch = colorlog.StreamHandler()
ch.setFormatter(colorlog.ColoredFormatter(FORMAT))
logger = logging.getLogger('pxTask')
logger.addHandler(ch)
logging_level = int(os.getenv('MASKT_LOGGING', '20'))


class pxLogging():
    def __init__(self):
        logger.setLevel(logging_level)
        self.logger = logging.getLogger(f'Maskt.{self.__class__.__name__}')

