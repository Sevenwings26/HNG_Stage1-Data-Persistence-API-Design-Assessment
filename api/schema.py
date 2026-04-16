from pydantic import BaseModel
from datetime import datetime


class ProfileResponse(BaseModel):
    id: str
    name: str
    gender: str
    gender_probability: float
    sample_size: int
    age: int
    age_group: str
    country_id: str
    country_probability: float
    created_at: datetime

    class Config:
        from_attributes = True

        