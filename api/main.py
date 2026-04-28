from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import httpx

from api.routers import auth, profiles, search
from api.dependencies.auth import get_current_user

# Lifespan (connection reuse)
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient()
    yield
    await app.state.client.aclose()

app = FastAPI(lifespan=lifespan)

# Middleware
app.add_middleware(SessionMiddleware, secret_key="SESSION_SECRET")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
# app.include_router(profiles.router, prefix="/api/profiles", tags=["Profiles"])
app.include_router(search.router, prefix="/api/profiles", tags=["Search"])

app.include_router(
    profiles.router,
    prefix="/api/profiles",
    dependencies=[Depends(get_current_user)]
)

# -----------------------------
# GET /
# -----------------------------
@app.get('/')
def root():
    return {
        "project": "Insighta Labs API",

        "slack_name": "Sevenwings",
        "github_repo": "https://github.com/Sevenwings26/HNG_Stage1-Data-Persistence-API-Design-Assessment.git",
        
        "usage": "https://hng-stage1-data-persistence-api-des-swart.vercel.app",
        "documentation": "https://hng-stage1-data-persistence-api-des-swart.vercel.app/docs",
    }


