"""
Tasks
==============

Provides access to
distributed task processing.
"""

from celery import Celery
from jobs import celery_config, mail_config

# For sending mail.
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from logger import logger
logger = logger(__name__)

celery = Celery()
celery.config_from_object(celery_config)

def workers():
    """
    Get info about currently available Celery workers.
    If none are available, or there are issues connecting
    to the MQ, returns False.

    Returns:
        | dict      -- dict of available workers.
        OR
        | bool      -- False if no available workers, or cannot connect ot MQ.
    """

    try:
        # Get info on available workers.
        workers = celery.control.inspect().stats()
        if not workers:
            logger.error('No Celery workers available.')
            return False
    except IOError as e:
        logger.error('Error connecting to MQ. Check that it is running.')
        return False

    logger.info('There are {0} workers available.'.format(len(workers)))
    return workers


def active():
    """
    Get info about currently executing tasks.
    """
    try:
        active_tasks = celery.control.inspect().active()
        if not active_tasks:
            logger.info('No active tasks.')
            return False
    except IOError as e:
        logger.error('Error connecting to MQ. Check that it is running.')
        return False

    logger.info('There are {0} executing tasks.'.format(len(active_tasks)))
    return active_tasks

@celery.task
def notify(body):
    """
    Send an e-mail notification.
    """
    from_addr = mail_config.USER

    # Construct the message.
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['Subject'] = 'Hello from your cloud!'
    msg.attach(MIMEText(body, 'plain'))

    # Connect to the mail server.
    server = smtplib.SMTP(mail_config.HOST, mail_config.PORT)
    server.starttls()
    server.login(from_addr, mail_conig.PASS)

    for target in mail_config.TARGETS:
        msg['To'] = target
        server.sendmail(from_addr, target, msg.as_string())

    server.quit()
