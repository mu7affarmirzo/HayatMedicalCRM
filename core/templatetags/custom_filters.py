from django import template

register = template.Library()


@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def sub(value, arg):
    """Subtract the argument from the value"""
    try:
        return value - arg
    except (ValueError, TypeError):
        return 0

@register.filter
def sub(value, arg):
    """Subtracts the arg from the value."""
    try:
        return value - arg
    except (ValueError, TypeError):
        try:
            return value or 0
        except:
            return 0

@register.filter
def divisibleby(value, arg):
    """
    Returns the percentage value/arg * 100
    """
    try:
        value = int(value)
        arg = int(arg)
        if arg:
            return (value / arg) * 100
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def format_phone(value):
    """
    Formats a phone number in the pattern +998 (XX) XXX-XX-XX
    Example: +998998887766 becomes +998 (99) 888-77-66
    """
    if not value:
        return ""

    # Remove any non-digit characters
    cleaned = ''.join(c for c in value if c.isdigit() or c == '+')

    # Handle Uzbekistan format (+998)
    if cleaned.startswith('+998') and len(cleaned) >= 12:
        return f"{cleaned[:4]} ({cleaned[4:6]}) {cleaned[6:9]}-{cleaned[9:11]}-{cleaned[11:13]}"

    # General fallback for other formats
    elif cleaned.startswith('+') and len(cleaned) > 10:
        # Try to format as international number
        country_code = cleaned[:4] if len(cleaned) >= 13 else cleaned[:3]
        remaining = cleaned[len(country_code):]
        parts = [remaining[i:i + 2] for i in range(0, len(remaining), 2)]
        formatted = '-'.join(parts)
        return f"{country_code} {formatted}"

    # If all else fails, just add some basic formatting
    elif len(cleaned) > 6:
        # For domestic number formats
        return f"{cleaned[:-6]}-{cleaned[-6:-3]}-{cleaned[-3:]}"

    # If we can't determine the format, return the original
    return value


@register.filter
def subtract(value, arg):
    """Subtracts the arg from the value."""
    try:
        return value - arg
    except (ValueError, TypeError):
        try:
            return int(value) - int(arg)
        except (ValueError, TypeError):
            return 0