from pydantic import BaseModel

from datetime import datetime


class Website(BaseModel):
    url: str