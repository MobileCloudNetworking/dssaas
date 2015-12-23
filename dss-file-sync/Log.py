import logging
from Config import *

def config_logger(name,log_level=logging.DEBUG):
    conf = Config()
    logging.basicConfig(format='%(levelname)s %(asctime)s %(module)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(conf.get('log', 'name'))
    logger.setLevel(log_level)
    handler = logging.FileHandler(conf.get('log', 'filename'))
    formatter = logging.Formatter(fmt='%(levelname)s %(asctime)s %(module)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

