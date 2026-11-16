"""One error shape for the whole API.

Every error response looks like:
    {"detail": "A human-readable message", "errors": {"field": ["message", ...]}}

`detail` is always a string the frontend can show to the user.
`errors` holds per-field messages (empty {} when the error is not about a field).
"""
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def first_message(value):
    """Dig out the first plain message from DRF's nested error data."""
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, (list, tuple)):
        for item in value:
            message = first_message(item)
            if message:
                return message
        return ''
    return str(value) if value else ''


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None  # unexpected server error: Django returns a plain 500

    if isinstance(exc, ValidationError):
        errors = response.data if isinstance(response.data, dict) else {'non_field_errors': response.data}
        detail = first_message(errors) or 'Invalid input.'
    else:
        errors = {}
        detail = str(response.data.get('detail', 'The request could not be completed.'))

    response.data = {'detail': detail, 'errors': errors}
    return response
