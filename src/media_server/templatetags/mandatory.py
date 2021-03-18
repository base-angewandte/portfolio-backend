from django import template

register = template.Library()


@register.filter
def must_have(value, fieldname):
    if not value:
        raise ValueError(f"Field '{fieldname}' is mandatory.")
    return True
