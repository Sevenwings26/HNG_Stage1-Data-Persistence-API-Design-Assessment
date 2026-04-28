import os
import enum
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, func, Enum, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from uuid_utils import uuid7

load_dotenv()

raw_url = os.getenv('DATABASE_URL')

# 2. Fix the 'postgres://' vs 'postgresql://' issue
if raw_url and raw_url.startswith("postgres://"):
    DATABASE_URL = raw_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_url

# 3. Create engine (Ensure you have pip install psycopg2-binary)
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base = declarative_base()

# model 
class UserRole(enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid7()))
    github_id = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=False)
    email = Column(String, index=True)
    avatar_url = Column(String)
    role = Column(Enum(UserRole), default=UserRole.ANALYST, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from datetime import datetime, timezone, timedelta

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid7()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)

    is_revoked = Column(Boolean, default=False, nullable=False)

    expires_at = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid7()))
    name = Column(String, unique=True, index=True, nullable=False)
    gender = Column(String)
    gender_probability = Column(Float)
    sample_size = Column(Integer)
    age = Column(Integer)
    age_group = Column(String)
    country_id = Column(String)
    country_probability = Column(Float)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()  # handles UTC
    )


