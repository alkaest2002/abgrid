from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    auth_secret: str = Field(..., env='AUTH_SECRET')
    token_lifetime_hours: int = Field(default=12, env='TOKEN_LIFETIME_HOURS')
    max_concurrent_requests: int = Field(default=10, env='MAX_CONCURRENT_REQUESTS')

    class Config:
        env_file = '.env'
        case_sensitive = False

    @classmethod
    @lru_cache()
    def load(cls):
        return cls()