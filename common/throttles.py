from rest_framework.throttling import AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    """
    10 requests/minute on login and register.
    Prevents brute-force attacks on credentials.
    Scope name 'auth' maps to DEFAULT_THROTTLE_RATES['auth'].
    """
    scope = 'auth'