from django import template

register = template.Library()

@register.filter
def kes(value):
    return f"KES {value:,.2f}"