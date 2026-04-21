import os
import json
import requests
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import SessionLocal, Profile
# from model import Profile

# Seed Data - 
# SEED_URL = "https://drive.google.com/file/d/1Up06dcS9OfUEnDj_u6OV_xTRntupFhPH/view"

SEED_URL = "https://drive.google.com/uc?export=download&id=1Up06dcS9OfUEnDj_u6OV_xTRntupFhPH"

"""
{
      "name": "Awino Hassan",
      "gender": "female",
      "gender_probability": 0.66,
      "age": 68,
      "age_group": "senior",
      "country_id": "TZ",
      "country_name": "Tanzania",
      "country_probability": 0.6
    },
"""


def seed_profiles():
    db: Session = SessionLocal()

    try:
        response = requests.get(SEED_URL)
        print(response.status_code)
        print(response.headers.get("content-type"))
        # print(response.text[:200])

        data = response.json()
        profiles = data.get("profiles", [])

        # print(len(profiles)) # count

        inserted = 0
        skipped = 0
        for item in profiles:
            name = item.get("name")

            if not isinstance(name, str):
                continue  # skip bad records safely

            normalized_name = name.strip().lower()

            # 2. Idempotency check... To avoid duplicate of same data
            existing = db.query(Profile).filter(
                func.lower(Profile.name) == normalized_name
            ).first()

            if existing:
                skipped += 1
                continue

            # 6. Persist - Save to DB..
            profile = Profile(
                name=normalized_name,
                gender=item["gender"],
                gender_probability=item["gender_probability"],
                age=item["age"],
                age_group=item["age_group"],
                country_id=item["country_id"],
                country_probability=item["country_probability"],
            )

            db.add(profile)
            inserted += 1
            
        db.commit()
        print(f"Inserted: {inserted}, Skipped: {skipped}")

    finally:
        db.close()
        # pass


if __name__ == "__main__":
    seed_profiles()

