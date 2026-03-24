from django.core.mail import send_mail
from django.conf import settings


def send_transactional_email(subject, message, to_emails, html_message=None):
    """
    Send a transactional email to one or more recipients.

    Args:
        subject (str): Email subject line.
        message (str): Plain-text email body.
        to_emails (list[str]): List of recipient email addresses.
        html_message (str | None): Optional HTML version of the body.
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        to_emails,
        html_message=html_message,
        fail_silently=False,
    )
