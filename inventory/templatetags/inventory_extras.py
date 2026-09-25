from django import template

register = template.Library()

@register.filter
def calculate_discount(days_to_expiry):
    try:
        days = int(days_to_expiry)
    except (ValueError, TypeError):
        return 0

    if days <= 0:
        return 50  # Expired items
    elif days <= 3:
        return 30  # Very close to expiry
    elif days <= 7:
        return 20  # Close to expiry
    elif days <= 14:
        return 10  # Approaching expiry
    else:
        return 0   # Fresh items

@register.filter
def clamp(value, args):
    """
    Usage: {{ value|clamp:"0,100" }}
    """
    try:
        val = float(value)
        min_val, max_val = map(float, args.split(','))
        return max(min_val, min(val, max_val))
    except Exception:
        return value
