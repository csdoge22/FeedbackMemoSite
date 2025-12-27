import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_DIR = os.path.join(BASE_DIR, "..", "env")

# Map environment → env file
ENV_FILE_MAP = {
    "development": os.path.join(ENV_DIR, "dev.env"),
    "testing": os.path.join(ENV_DIR, "test.env"),
    "production": os.path.join(ENV_DIR, "prod.env"),
}


class Settings(BaseSettings):
    # -------------------------
    # Application settings
    # -------------------------
    app_env: str = "development"
    debug: bool = True
    secret_key: str

    # -------------------------
    # Database settings
    # -------------------------
    # Optional pieces (not required if DATABASE_URL is set)
    db_user: str | None = None
    db_password: str | None = None
    db_host: str | None = None
    db_port: int = 5432
    db_name: str | None = None

    # Master override used in testing
    database_url: str | None = None

    # -------------------------
    # Build DB URL
    # -------------------------
    def get_db_url(self) -> str:
        """
        Priority:
        1. database_url → explicitly set in env (used in testing)
        2. build URL from db_user/db_password/etc
        """
        if self.database_url:
            return self.database_url

        if not all([self.db_user, self.db_password, self.db_host, self.db_name]):
            raise ValueError(
                "Database configuration incomplete. "
                "Set DATABASE_URL or all DB_USER/DB_PASSWORD/DB_HOST/DB_NAME."
            )

        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # -------------------------
    # Pydantic v2 config
    # -------------------------
    model_config = ConfigDict(
        extra="allow",
        env_file=ENV_FILE_MAP.get(
            # Detect pytest automatically → force test.env
            "testing" if "PYTEST_CURRENT_TEST" in os.environ
            else os.environ.get("APP_ENV", "development")
        ),
    )


# Instantiate settings
settings = Settings()

# -------------------------
# TEST_DB_URL becomes available globally
# -------------------------
TEST_DB_URL = settings.database_url if settings.app_env == "testing" else None
