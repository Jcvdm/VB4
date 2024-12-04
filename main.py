from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import os
from datetime import datetime
from models import SearchQuery, ProgressEntry
from progress_tracker import ProgressTracker
from storage_service import ProgressStorage
from typing import List

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Code Progress Tracking API",
    description="API for tracking and searching code development progress",
    version="1.0.0"
)

# Initialize services
tracker = ProgressTracker(os.getenv("CODE_REPO_PATH"))
storage = ProgressStorage(os.getenv("VECTOR_DB_PATH"))

@app.post("/progress/", response_model=ProgressEntry)
async def create_progress(
    title: str,
    description: str,
    category: str,
    tags: List[str] = None,
    impact_level: str = "minor"
):
    """Create a new progress entry from recent git changes"""
    try:
        entry = tracker.create_progress_entry(
            title=title,
            description=description,
            category=category,
            tags=tags,
            impact_level=impact_level
        )
        storage.add_entry(entry)
        return entry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/", response_model=List[ProgressEntry])
async def search_progress(query: SearchQuery):
    """Search for progress entries using vector similarity"""
    try:
        results = storage.search(query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories/")
async def get_categories():
    """Get list of available categories"""
    return [
        "feature",
        "bugfix",
        "refactor",
        "testing",
        "ui",
        "other"
    ]

@app.get("/health/")
async def health_check():
    """Check if the service is healthy"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "git_repo": os.getenv("CODE_REPO_PATH"),
        "vector_store": os.getenv("VECTOR_DB_PATH")
    }

@app.post("/sync/")
async def sync_from_git():
    """Sync recent changes from git and create progress entries"""
    try:
        changes = tracker.get_recent_changes(
            since=datetime.now().replace(hour=0, minute=0)
        )
        
        # Group changes by category
        changes_by_category = {}
        for change in changes:
            if change.category not in changes_by_category:
                changes_by_category[change.category] = []
            changes_by_category[change.category].append(change)
        
        # Create progress entries for each category
        entries = []
        for category, category_changes in changes_by_category.items():
            if not category_changes:
                continue
                
            # Create a summary of changes
            summary = f"Daily progress update: {len(category_changes)} {category} changes"
            description = "Automated progress entry from git changes:\n\n"
            description += "\n".join(f"- {c.description}" for c in category_changes)
            
            entry = tracker.create_progress_entry(
                title=summary,
                description=description,
                category=category,
                tags=[category],
                impact_level="minor"
            )
            storage.add_entry(entry)
            entries.append(entry)
            
        return {
            "message": f"Successfully synced {len(changes)} changes",
            "entries_created": len(entries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
