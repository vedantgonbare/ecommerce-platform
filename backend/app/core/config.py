from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "E-Commerce Platform"
    database_url: str 
    jwt_secret_key: str

    class Config:
        env_file = ".env"

settings = Settings()