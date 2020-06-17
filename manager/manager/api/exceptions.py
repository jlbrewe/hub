from rest_framework import exceptions, status


class AccountQuotaExceeded(exceptions.APIException):
    """
    A custom API exception for when an account quota is exceeded.

    Should be instantiated with a diction of details.
    """

    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "An account quota was exceeded"


class ConflictError(exceptions.APIException):
    """
    A custom API exception for conflict errors.

    Should be used when the request data is valid but fails
    due to a conflict of some sort e.g. a uniqueness constraint.
    Such an exception does not exist in DRF. Although see:
    https://github.com/encode/django-rest-framework/issues/1848
    """

    status_code = status.HTTP_409_CONFLICT
    default_detail = "A conflict occurred"
