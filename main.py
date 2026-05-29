"""
Snip — URL Shortener API

Endpoints:
  POST /api/shorten        — shorten a URL
  GET  /{short_code}       — redirect to original URL (301)
  GET  /api/stats/{code}   — get click stats for a short code
"""

import os
import random
import string
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import URL

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# ── Lifespan ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


# ── App ─────────────────────────────────────────────────────

app = FastAPI(
    title="Snip API",
    description="URL shortener service",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://kennyy.me,http://localhost:3456,http://localhost:5500,http://127.0.0.1:5500",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ─────────────────────────────────────────────────

class ShortenRequest(BaseModel):
    url: HttpUrl


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str


class StatsResponse(BaseModel):
    url: str
    short_code: str
    short_url: str
    clicks: int
    created_at: str


# ── Helpers ─────────────────────────────────────────────────

CHARSET = string.ascii_lowercase + string.digits
CODE_LENGTH = 6


def generate_short_code(db: Session) -> str:
    """Generate a unique 6-char alphanumeric code."""
    for _ in range(10):
        code = "".join(random.choices(CHARSET, k=CODE_LENGTH))
        exists = db.query(URL).filter(URL.short_code == code).first()
        if not exists:
            return code
    raise RuntimeError("Failed to generate a unique short code after 10 attempts")


# ── Routes ──────────────────────────────────────────────────

@app.post("/api/shorten", response_model=ShortenResponse, status_code=201)
def shorten_url(body: ShortenRequest, db: Session = Depends(get_db)):
    """
    Accept a long URL and return a shortened version.
    If the URL was already shortened, return the existing short code.
    """
    original = str(body.url)

    # Check if this URL was already shortened
    existing = db.query(URL).filter(URL.original_url == original).first()
    if existing:
        return ShortenResponse(
            short_code=existing.short_code,
            short_url=f"{BASE_URL}/{existing.short_code}",
        )

    # Create new short URL
    code = generate_short_code(db)
    url_entry = URL(short_code=code, original_url=original)
    db.add(url_entry)
    db.commit()
    db.refresh(url_entry)

    return ShortenResponse(
        short_code=url_entry.short_code,
        short_url=f"{BASE_URL}/{url_entry.short_code}",
    )


@app.get("/api/stats/{short_code}", response_model=StatsResponse)
def get_stats(short_code: str, db: Session = Depends(get_db)):
    """Return click stats for a short code."""
    url_entry = db.query(URL).filter(URL.short_code == short_code).first()
    if not url_entry:
        raise HTTPException(status_code=404, detail="Short code not found")

    return StatsResponse(
        url=url_entry.original_url,
        short_code=url_entry.short_code,
        short_url=f"{BASE_URL}/{url_entry.short_code}",
        clicks=url_entry.clicks,
        created_at=url_entry.created_at.isoformat(),
    )


@app.get("/{short_code}")
def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    """
    Redirect to the original URL.
    Increments the click counter on each redirect.
    """
    url_entry = db.query(URL).filter(URL.short_code == short_code).first()
    if not url_entry:
        raise HTTPException(status_code=404, detail="Short code not found")

    # Increment clicks
    url_entry.clicks += 1
    db.commit()

    return RedirectResponse(url=url_entry.original_url, status_code=301)


@app.get("/")
def health_check():
    """Health check / root endpoint."""
    return {"status": "ok", "service": "snip"}
