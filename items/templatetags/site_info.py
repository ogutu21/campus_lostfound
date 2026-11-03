import os

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def contact_email():
    """Where students can reach whoever runs the site.

    Set CONTACT_EMAIL in .env to choose it. Otherwise we use the project
    mailbox that the site already sends its notifications from.
    """
    return os.environ.get("CONTACT_EMAIL") or settings.EMAIL_HOST_USER