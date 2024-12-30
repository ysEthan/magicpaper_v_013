from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    """将两个数相乘"""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except:
        return 0 