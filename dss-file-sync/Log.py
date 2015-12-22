__author__ = 'Santi'

import logging

def config_logger(name,log_level=logging.DEBUG):
    logging.basicConfig(format='%(levelname)s %(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        log_level=log_level)
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    handler = logging.FileHandler('torrent.log')
    formatter = logging.Formatter(fmt='%(levelname)s %(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

