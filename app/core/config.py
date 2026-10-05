from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RoadSide Fix API"
    app_env: str = "development"

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    redis_url: str = "redis://localhost:6379/0"

    razorpay_key_id: str
    razorpay_key_secret: str
    # razorpay_webhook_secret: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


settings = Settings()