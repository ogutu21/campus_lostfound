import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def notify(user, subject, message, path, always=False):
    """Email `user`, with a link to `path` on the site.

    Returns True if the email was sent, False if it was skipped or failed.
    `always=True` ignores the user's "email me" setting. It is used for
    service notices about their own posts, such as "your post is coming down".

    Never raises: a mail problem must not break the page that triggered it.
    """
    if not user.email:
        return False
    if not always and not user.email_notifications:
        return False

    body = (
        f"Hi {user.first_name},\n\n"
        f"{message}\n\n"
        f"Open it here: {settings.SITE_URL}{path}\n\n"
        "-- \n"
        "Campus Lost & Found. You can switch most of these emails off under Settings."
    )
    try:
        send_mail(subject, body, None, [user.email], fail_silently=False)
    except Exception:
        logger.exception("Could not send an email to user %s", user.pk)
        return False
    return True