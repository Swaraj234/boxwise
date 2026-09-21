from rest_framework import status
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Custom exception handler to format error responses into a consistent schema:
    {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Human readable message",
            "details": {...}
        }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_code = "VALIDATION_ERROR"
        if response.status_code == status.HTTP_404_NOT_FOUND:
            error_code = "NOT_FOUND"
        elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            error_code = "METHOD_NOT_ALLOWED"
        elif response.status_code >= 500:
            error_code = "INTERNAL_SERVER_ERROR"

        custom_data = {
            "error": {
                "code": error_code,
                "message": _extract_message(response.data),
                "details": response.data,
            }
        }
        response.data = custom_data

    return response


def _extract_message(data) -> str:
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        for key, val in data.items():
            if isinstance(val, list) and len(val) > 0:
                return f"{key}: {val[0]}"
            elif isinstance(val, str):
                return f"{key}: {val}"
        return "Validation failed."
    elif isinstance(data, list) and len(data) > 0:
        return str(data[0])
    return str(data)
