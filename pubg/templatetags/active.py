import re
from django import template

register = template.Library()

import sys


@register.simple_tag
def active(request, pattern):
    """Returns active if the request URL contains pattern"""
    if re.search(pattern, request.path):
        return "active"
    return ""
