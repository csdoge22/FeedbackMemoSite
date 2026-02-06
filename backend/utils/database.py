"""
DEPRECATED: Use core.database instead.

This module is kept for backward compatibility only.
All new code should import from core.database.
"""
import warnings
from core.database import create_db_and_tables, get_session, engine  # noqa: F401

warnings.warn(
    "utils.database is deprecated. Use core.database instead.",
    DeprecationWarning,
    stacklevel=2,
)

