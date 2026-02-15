"""
Database Initialization Script

Run this to set up the database for production deployment.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import init_db, get_db_context
from app.models.database import Concept


async def load_concepts():
    """Load concepts from JSON into database."""
    concepts_path = Path(__file__).parent.parent.parent / "data" / "concepts.json"
    
    if not concepts_path.exists():
        print(f"Concepts file not found: {concepts_path}")
        return 0
    
    async with get_db_context() as db:
        from sqlalchemy import select
        
        # Check if concepts already loaded
        result = await db.execute(select(Concept).limit(1))
        if result.scalar_one_or_none():
            print("Concepts already loaded")
            return 0
        
        with open(concepts_path, "r", encoding="utf-8") as f:
            concepts_data = json.load(f)
        
        count = 0
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
            count += 1
        
        await db.commit()
        return count


async def main():
    """Initialize database and load initial data."""
    print("=" * 50)
    print("Pensieve Database Initialization")
    print("=" * 50)
    
    # Initialize tables
    print("\n1. Creating database tables...")
    await init_db()
    print("   ✓ Tables created")
    
    # Load concepts
    print("\n2. Loading concept database...")
    count = await load_concepts()
    if count > 0:
        print(f"   ✓ Loaded {count} concepts")
    else:
        print("   → Concepts already exist or file not found")
    
    print("\n" + "=" * 50)
    print("Database initialization complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
