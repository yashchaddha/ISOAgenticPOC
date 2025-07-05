# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    mongodb_uri: str
    s3_bucket: str
    aws_region: str = "ap-east-1"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",      # drop any env vars not declared above
    )

    # class Config:
    #     env_file = ".env"

settings = Settings()
