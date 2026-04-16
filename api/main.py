import asyncio
from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
import httpx
from contextlib import asynccontextmanager
from .database import get_db, Profile
from .schema import ProfileResponse, ProfileRequest


# Performance Hack: Use a Lifespan to keep one connection open
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs when the server starts
    app.state.client = httpx.AsyncClient()
    yield
    # This runs when the server stops
    await app.state.client.aclose()

# initialize app 
app = FastAPI(lifespan=lifespan)


# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper: Age Group Classifier
def classify_age_group(age: int) -> str:
    if age <= 12:
        return "child"
    elif age <= 19:
        return "teenager"
    elif age <= 59:
        return "adult"
    return "senior"


# GET
@app.get('/')
def root():
    return {
        "project": "Stage 1: Data Persistence & API Design Assessment",

        "slack_name": "Sevenwings",
        "github_repo": "https://github.com/Sevenwings26/HNG_Stage1-Data-Persistence-API-Design-Assessment.git",
        
        
        "usage": "https://hng-stage1-data-persistence-api-des-swart.vercel.app",
        "documentation": "https://hng-stage1-data-persistence-api-des-swart.vercel.app/docs",
    }


# POST /api/profiles
@app.post("/api/profiles", status_code=201)
async def create_profile(
    paylaod: ProfileRequest,
    db: Session = Depends(get_db)
):
    name = paylaod.name
    # 1. Validation - if not empty
    if not name or name.strip() == "":
        raise HTTPException(status_code=400, detail="Missing or empty name")

    normalized_name = name.strip().lower()

    # 2. Idempotency check... To avoid duplicate of same data
    existing = db.query(Profile).filter(
        func.lower(Profile.name) == normalized_name
    ).first()

    if existing:
        return {
            "status": "success",
            "message": "Profile already exists",
            "data": existing
        }

    # 3. Concurrent API calls
    async with httpx.AsyncClient(timeout=5.0) as client:
        gender_task = client.get(f"https://api.genderize.io?name={normalized_name}")
        age_task = client.get(f"https://api.agify.io?name={normalized_name}")
        country_task = client.get(f"https://api.nationalize.io?name={normalized_name}")

        gender_res, age_res, country_res = await asyncio.gather(
            gender_task, age_task, country_task
        )

    # collect data 
    gen_data = gender_res.json()
    age_data = age_res.json()
    nat_data = country_res.json()

    # 4. Edge case validation (STRICT)
    if (
        gen_data.get("gender") is None
        or gen_data.get("count", 0) == 0
        or age_data.get("age") is None
        or not nat_data.get("country")
    ):
        raise HTTPException(status_code=502, detail="Upstream failure")

    # 5. Process data
    age = age_data["age"]
    age_group = classify_age_group(age)

    top_country = max(
        nat_data["country"],
        key=lambda x: x["probability"]
    )

    # 6. Persist - Save to DB..
    profile = Profile(
        name=normalized_name,
        gender=gen_data["gender"],
        gender_probability=gen_data["probability"],
        sample_size=gen_data["count"],
        age=age,
        age_group=age_group,
        country_id=top_country["country_id"],
        country_probability=top_country["probability"],
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "status": "success",
        "data": profile
    }


# -----------------------------
# GET /api/profiles/{id}
# -----------------------------
# @app.get("/api/profiles/{id}")
# def get_profile(id: str, db: Session = Depends(get_db)):
#     profile = db.query(Profile).filter(Profile.id == id).first()

#     if not profile:
#         raise HTTPException(status_code=404, detail="Profile not found")

#     return {
#         "status": "success",
#         "data": profile
#     }


@app.get("/api/profiles/{id}")
def get_profile(id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "status": "success",
        "data": ProfileResponse.model_validate(profile)
    }

# -----------------------------
# GET /api/profiles
# -----------------------------
@app.get("/api/profiles")
def list_profiles(
    gender: str | None = None,
    country_id: str | None = None,
    age_group: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Profile)

    if gender:
        query = query.filter(func.lower(Profile.gender) == gender.lower())

    if country_id:
        query = query.filter(func.lower(Profile.country_id) == country_id.lower())

    if age_group:
        query = query.filter(func.lower(Profile.age_group) == age_group.lower())

    results = query.all()

    return {
        "status": "success",
        "count": len(results),
        "data": results
    }


# -----------------------------
# DELETE /api/profiles/{id}
# -----------------------------
@app.delete("/api/profiles/{id}", status_code=204)
def delete_profile(id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    db.delete(profile)
    db.commit()


