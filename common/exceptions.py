from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            'status': 'error',
            'code': response.status_code,
            'errors': response.data,
            'message': _get_message(response.data),
        }

    return response


def _get_message(data):
    if isinstance(data, list):
        return str(data[0]) if data else 'An error occurred.'
    if isinstance(data, dict):
        for value in data.values():
            return str(value[0]) if isinstance(value, list) else str(value)
    return str(data)
