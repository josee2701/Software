from django import template

register = template.Library()


@register.filter(name="get_with_default")
def get_with_default(value, arg):
    return value.get(arg, "")
