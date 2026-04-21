import re
import asyncio
import httpx
from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from contextlib import asynccontextmanager
from api.database import get_db, Profile
from api.schema import ProfileResponse, ProfileRequest
from fastapi import Query
from sqlalchemy import desc, asc


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


# -----------------------------
# GET /
# -----------------------------
@app.get('/')
def root():
    return {
        "project": "Stage 1: Data Persistence & API Design Assessment",

        "slack_name": "Sevenwings",
        "github_repo": "https://github.com/Sevenwings26/HNG_Stage1-Data-Persistence-API-Design-Assessment.git",
        
        "usage": "https://hng-stage1-data-persistence-api-des-swart.vercel.app",
        "documentation": "https://hng-stage1-data-persistence-api-des-swart.vercel.app/docs",
    }


# -----------------------------
# POST /api/profiles
# -----------------------------
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
# GET /api/profiles
# -----------------------------
@app.get("/api/profiles")
def list_profiles(
    # Filters
    gender: str | None = None,
    country_id: str | None = None,
    age_group: str | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
    min_gender_probability: float | None = None,
    min_country_probability: float | None = None,
    # Sorting & Pagination
    sort_by: str = "created_at",
    order: str = "desc",
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(Profile)

    # 1. Advanced Filtering Logic
    if gender:
        query = query.filter(func.lower(Profile.gender) == gender.lower())
    if country_id:
        query = query.filter(func.lower(Profile.country_id) == country_id.lower())
    if age_group:
        query = query.filter(func.lower(Profile.age_group) == age_group.lower())
    
    # Range Filters (The "Intelligence" part)
    if min_age is not None:
        query = query.filter(Profile.age >= min_age)
    if max_age is not None:
        query = query.filter(Profile.age <= max_age)
    if min_gender_probability is not None:
        query = query.filter(Profile.gender_probability >= min_gender_probability)
    if min_country_probability is not None:
        query = query.filter(Profile.country_probability >= min_country_probability)

    # 2. Sorting Logic
    # Map the user input string to the actual Database Columns
    allowed_sort_columns = {
        "age": Profile.age,
        "created_at": Profile.created_at,
        "gender_probability": Profile.gender_probability
    }
    
    target_column = allowed_sort_columns.get(sort_by, Profile.created_at)
    
    if order.lower() == "asc":
        query = query.order_by(asc(target_column))
    else:
        query = query.order_by(desc(target_column))

    # 3. Pagination Logic
    total_records = query.count()
    skip = (page - 1) * limit
    results = query.offset(skip).limit(limit).all()

    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total_records,
        # "data": results,
        "data": [ProfileResponse.model_validate(p) for p in results]
        # "data": [ProfileResponse.model_validate(p) for p in results]

    }


# -----------------------------
# GET /api/profiles/search
# -----------------------------
# Mapping for common countries in the seed data
COUNTRY_MAP = {
    "nigeria": "NG",
    "kenya": "KE",
    "angola": "AO",
    "tanzania": "TZ",
    "ghana": "GH",
    "uganda": "UG"
}

@app.get("/api/profiles/search")
def natural_language_search(
    q: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    if not q or q.strip() == "":
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid query parameters"}
        )

    query = db.query(Profile)
    text = q.lower().strip()
    interpreted = False

    # Gender
    if "female" in text:
        query = query.filter(func.lower(Profile.gender) == "female")
        interpreted = True
    elif "male" in text:
        query = query.filter(func.lower(Profile.gender) == "male")
        interpreted = True

    # Age groups
    if "young" in text:
        query = query.filter(Profile.age >= 16, Profile.age <= 24)
        interpreted = True

    if "child" in text:
        query = query.filter(Profile.age_group == "child")
        interpreted = True

    if "teenager" in text:
        query = query.filter(Profile.age_group == "teenager")
        interpreted = True

    if "adult" in text:
        query = query.filter(Profile.age_group == "adult")
        interpreted = True

    if "senior" in text:
        query = query.filter(Profile.age_group == "senior")
        interpreted = True

    # Numeric parsing
    age_match = re.search(r'(above|over|below|under|at)\s+(\d+)', text)
    if age_match:
        condition, value = age_match.groups()
        value = int(value)

        if condition in ["above", "over"]:
            query = query.filter(Profile.age > value)
        elif condition in ["below", "under"]:
            query = query.filter(Profile.age < value)
        elif condition == "at":
            query = query.filter(Profile.age == value)

        interpreted = True

    # Country
    for country_name, code in COUNTRY_MAP.items():
        if country_name in text:
            query = query.filter(Profile.country_id == code)
            interpreted = True
            break

    if not interpreted:
        return JSONResponse(
            status_code=422,
            content={"status": "error", "message": "Unable to interpret query"}
        )

    total = query.count()
    skip = (page - 1) * limit
    results = query.offset(skip).limit(limit).all()

    return {
        "status": "success",
        "page": page,
        "limit": limit,
        "total": total,
        # "data": results
        "data": [ProfileResponse.model_validate(p) for p in results]
    }


# -----------------------------
# GET /api/profiles{id}
# -----------------------------
@app.get("/api/profiles/{id}")
def get_profile(id: str, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "status": "success",
    #   "data": profile
        "data": ProfileResponse.model_validate(profile)
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


