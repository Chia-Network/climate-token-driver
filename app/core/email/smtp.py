import smtplib
from typing import List
from app.config import settings
from app.logger import logger


def send_email(to: List[str], subject: str, body: str):
    email_text = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (settings.EMAIL_FROM_USER, ", ".join(to), subject, body)

    try:
        smtp_server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
        smtp_server.ehlo()
        smtp_server.login(settings.EMAIL_FROM_USER, settings.EMAIL_FROM_PASSWORD)
        smtp_server.sendmail(settings.EMAIL_FROM_USER, to, email_text)
        smtp_server.close()

        logger.debug("Email sent successfully!")
    except Exception as ex:
        logger.error("Something went wrong….", ex)
