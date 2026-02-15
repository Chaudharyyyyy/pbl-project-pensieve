"""
Concept Database Population Script

Populates the concepts table with curated psychological/philosophical entries.
"""

import asyncio
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


async def populate_concepts(database_url: str, concepts_path: str):
    """
    Load concepts from JSON and insert into database with embeddings.
    """
    # Load concepts
    with open(concepts_path, "r", encoding="utf-8") as f:
        concepts = json.load(f)
    
    print(f"Loaded {len(concepts)} concepts from {concepts_path}")
    
    # Initialize embedding model
    print("Loading embedding model...")
    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Connect to database
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Clear existing concepts (optional - comment out to append)
        # await session.execute(text("DELETE FROM concepts"))
        
        for concept in concepts:
            # Generate embedding
            text_for_embedding = f"{concept['name']} {concept['description']}"
            embedding = encoder.encode(text_for_embedding).tolist()
            
            # Insert concept
            await session.execute(
                text("""
                    INSERT INTO concepts 
                    (name, category, subcategory, description, source_citation, source_year, tags, embedding)
                    VALUES (:name, :category, :subcategory, :description, :source_citation, :source_year, :tags, :embedding)
                    ON CONFLICT (name) DO UPDATE SET
                        description = EXCLUDED.description,
                        embedding = EXCLUDED.embedding
                """),
                {
                    "name": concept["name"],
                    "category": concept["category"],
                    "subcategory": concept.get("subcategory"),
                    "description": concept["description"],
                    "source_citation": concept["source_citation"],
                    "source_year": concept.get("source_year"),
                    "tags": concept.get("tags", []),
                    "embedding": embedding,
                }
            )
            print(f"  Inserted: {concept['name']}")
        
        await session.commit()
    
    print(f"\nSuccessfully populated {len(concepts)} concepts")


if __name__ == "__main__":
    import sys
    
    database_url = sys.argv[1] if len(sys.argv) > 1 else "postgresql+asyncpg://pensieve:pensieve@localhost:5432/pensieve"
    concepts_path = sys.argv[2] if len(sys.argv) > 2 else "../data/concepts.json"
    
    asyncio.run(populate_concepts(database_url, concepts_path))
