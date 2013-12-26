"""
Logger
==============

Logger!
"""

import logging
from os import path

log_path = path.join(path.dirname(__file__), 'logs/log.log')

def logger(name):
    # Create the logger.
    logger = logging.getLogger(name)

    # Configure the logger.
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Output to file.
    fh = logging.FileHandler(log_path)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Output to console.
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
