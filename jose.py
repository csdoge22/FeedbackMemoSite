"""
Minimal shim for `jose` used in tests.

This file provides a tiny replacement for `jose.jwt.encode/decode`
and the exception types used by the application so tests can run
without installing the full `python-jose` package. It is intentionally
small and should only be used in test environments.
"""
from datetime import datetime


class JWTError(Exception):
    pass


class ExpiredSignatureError(JWTError):
    pass


class _JWT:
    @staticmethod
    def encode(payload, secret, algorithm=None):
        # Simple deterministic token format: TESTTOKEN:<sub>
        sub = payload.get("sub")
        return f"TESTTOKEN:{sub}"

    @staticmethod
    def decode(token, secret, algorithms=None):
        if not isinstance(token, str) or not token.startswith("TESTTOKEN:"):
            raise JWTError("Invalid token")
        try:
            _, sub = token.split(":", 1)
            return {"sub": sub}
        except Exception:
            raise JWTError("Invalid token format")


jwt = _JWT()
