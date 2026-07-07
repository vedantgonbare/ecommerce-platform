from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "E-Commerce Platform"
    database_url: str = "postgresql://postgres:postgres123@localhost:5432/ecommerce_db"

    class config:
        env_file = ".env"

settings = Settings()