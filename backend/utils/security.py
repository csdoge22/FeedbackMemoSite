"""
DEPRECATED: Use core.security instead.

This module is kept for backward compatibility only.
All new code should import from core.security.
"""
import warnings
from core.security import hash_password, verify_password  # noqa: F401

warnings.warn(
    "utils.security is deprecated. Use core.security instead.",
    DeprecationWarning,
    stacklevel=2,
)

