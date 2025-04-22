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


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_verbose_field_name(obj, field_name):
    """
    Returns the verbose name of a field.
    """
    return obj._meta.get_field(field_name).verbose_name


@register.filter
def get_field_value(obj, field_name):
    """
    Returns the value of a field.
    """
    field = obj._meta.get_field(field_name)
    value = getattr(obj, field_name)

    # Handle choices fields
    if hasattr(field, 'choices') and field.choices:
        get_display = getattr(obj, f'get_{field_name}_display', None)
        if get_display:
            return get_display()

    # Handle foreign keys
    if value and field.remote_field and field.remote_field.model:
        return str(value)

    return value


@register.filter
def get_id_for_field(fields_dict, field_name):
    """
    Returns the HTML ID for a form field.
    """
    return f'id_{field_name}'


@register.filter
def get_label_for_field(fields_dict, field_name):
    """
    Returns the label for a form field.
    """
    if field_name in fields_dict:
        return fields_dict[field_name].label
    return field_name


@register.filter
def field_has_error(errors, field_name):
    """
    Returns True if the field has errors.
    """
    return field_name in errors


@register.filter
def get_error_for_field(errors, field_name):
    """
    Returns the error message for a field.
    """
    if field_name in errors:
        return errors[field_name]
    return ""


@register.filter
def field_has_help_text(fields_dict, field_name):
    """
    Returns True if the field has help text.
    """
    if field_name in fields_dict:
        return bool(fields_dict[field_name].help_text)
    return False


@register.filter
def get_help_text(fields_dict, field_name):
    """
    Returns the help text for a field.
    """
    if field_name in fields_dict:
        return fields_dict[field_name].help_text
    return ""


@register.filter
def render_field(form, field_name):
    """
    Renders a form field with appropriate CSS classes.
    """
    if field_name in form.fields:
        field = form[field_name]
        widget_attrs = field.field.widget.attrs

        # Add Bootstrap classes
        if 'class' in widget_attrs:
            widget_attrs['class'] += ' form-control'
        else:
            widget_attrs['class'] = 'form-control'

        # Add error class if needed
        if field.errors:
            widget_attrs['class'] += ' is-invalid'

        return field
    return ""