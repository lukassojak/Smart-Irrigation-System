from pydantic import BaseModel


class Logging(BaseModel):
    enabled: bool
    log_level: str