import os

from django import template

register = template.Library()


@register.filter(name='filename_without_path')
def filename_without_path(arg):
    """Removes file path saved in the FileField and returns just the filename"""
    file_name = os.path.basename(arg)
    return file_name
