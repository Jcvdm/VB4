from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class CodeChange(BaseModel):
    """Represents a code change or commit"""
    id: str
    timestamp: datetime
    files_changed: List[str]
    description: str
    category: str
    commit_hash: Optional[str]
    metadata: Dict[str, str] = {}

class ProgressEntry(BaseModel):
    """Represents a development progress entry"""
    id: str
    date: datetime
    title: str
    description: str
    changes: List[CodeChange]
    category: str
    tags: List[str] = []
    impact_level: str = "minor"  # minor, major, critical

class SearchQuery(BaseModel):
    """Search parameters for querying the progress database"""
    query: str
    categories: Optional[List[str]] = None
    date_range: Optional[tuple[datetime, datetime]] = None
    tags: Optional[List[str]] = None
