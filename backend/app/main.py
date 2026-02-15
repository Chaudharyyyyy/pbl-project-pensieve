"""
Simplified Main Application for Local Development

FastAPI app with SQLite database and inline concept loading.
"""

from contextlib import asynccontextmanager
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")
    print(f"Database: {settings.database_url}")
    
    # Initialize database tables
    print("Initializing database...")
    await init_db()
    print("Database ready!")
    
    # Load concepts into database
    await load_concepts()
    
    yield
    
    # Shutdown
    print("Shutting down...")


async def load_concepts():
    """Load concepts from JSON into database."""
    from app.core.database import get_db_context
    from app.models.database import Concept
    from sqlalchemy import select
    
    concepts_path = Path(__file__).parent.parent.parent / "data" / "concepts.json"
    
    if not concepts_path.exists():
        print(f"Concepts file not found: {concepts_path}")
        return
    
    async with get_db_context() as db:
        # Check if concepts already loaded
        result = await db.execute(select(Concept).limit(1))
        if result.scalar_one_or_none():
            print("Concepts already loaded")
            return
        
        with open(concepts_path, "r", encoding="utf-8") as f:
            concepts_data = json.load(f)
        
        for concept in concepts_data:
            db_concept = Concept(
                name=concept["name"],
                category=concept["category"],
                subcategory=concept.get("subcategory"),
                description=concept["description"],
                source_citation=concept["source_citation"],
                source_year=concept.get("source_year"),
                tags_json=json.dumps(concept.get("tags", [])),
            )
            db.add(db_concept)
        
        await db.commit()
        print(f"Loaded {len(concepts_data)} concepts")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Privacy-first reflective journaling with ML-powered insights.",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import and include routers
from app.api.routes import auth, entries, reflections, concepts

app.include_router(auth.router, prefix="/api")
app.include_router(entries.router, prefix="/api")
app.include_router(reflections.router, prefix="/api")
app.include_router(concepts.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Privacy-first reflective journaling API",
        "docs": "/api/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
