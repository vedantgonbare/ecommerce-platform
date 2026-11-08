from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "E-Commerce Platform"
    database_url: str 
    jwt_secret_key: str
    redis_url: str
    stripe_secret_key: str
    stripe_webhook_secret: str
    frontend_url: str = "http://localhost:5173"
    cookie_secure: bool = False

settings = Settings()