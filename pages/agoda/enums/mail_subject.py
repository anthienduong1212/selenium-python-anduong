try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum


class MailSubject(StrEnum):
    OTP_MAIL_SUBJECT = "Your email OTP for Agoda"
