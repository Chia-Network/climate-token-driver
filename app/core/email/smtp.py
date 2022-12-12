import smtplib
from typing import List
from app.config import settings
from app.logger import logger


def send_email(to: List[str], subject: str, body: str):
    try:

        smtp = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        smtp.starttls() 
        smtp.login(settings.EMAIL_FROM_USER, settings.EMAIL_FROM_PASSWORD)
        message = "Subject: {}\n\n{}".format(subject, body)
        smtp.sendmail(settings.EMAIL_FROM_USER, to, message) 

        smtp.quit()

        logger.debug("Email sent successfully!")
    except Exception as ex:
        logger.error("Something went wrong….", ex)
