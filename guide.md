# Local Vector Database with LLM Integration - Code Progress Tracking

## Prerequisites
- Python 3.8+
- Docker (for running Qdrant)
- OpenAI API key

## Step 1: Project Setup

1. **Create Project Structure**
   ```bash
   mkdir VB3
   cd VB3
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install fastapi uvicorn langchain faiss-cpu transformers sentence-transformers python-dotenv gitpython
   ```

3. **Create Configuration**
   Create `.env` file:
   ```
   OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
   CODE_REPO_PATH=/path/to/your/code/repo
   VECTOR_DB_PATH=./vector_store
   ```

## Step 2: Core Components Implementation

### 1. Data Models (`models.py`)
```python
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
```

### 2. Code Progress Tracker (`progress_tracker.py`)
```python
from git import Repo
import os
from datetime import datetime
from models import CodeChange, ProgressEntry
from typing import List

class ProgressTracker:
    def __init__(self, repo_path: str):
        self.repo = Repo(repo_path)
        
    def get_recent_changes(self, since: datetime) -> List[CodeChange]:
        """Extract recent code changes from git history"""
        changes = []
        for commit in self.repo.iter_commits(since=since):
            change = CodeChange(
                id=str(len(changes)),
                timestamp=datetime.fromtimestamp(commit.committed_date),
                files_changed=[diff.a_path for diff in commit.diff()],
                description=commit.message,
                category=self._categorize_commit(commit),
                commit_hash=commit.hexsha,
                metadata={
                    "author": str(commit.author),
                    "lines_added": commit.stats.total["insertions"],
                    "lines_deleted": commit.stats.total["deletions"]
                }
            )
            changes.append(change)
        return changes

    def _categorize_commit(self, commit) -> str:
        """Categorize commit based on files changed and message"""
        msg = commit.message.lower()
        files = [diff.a_path for diff in commit.diff()]
        
        if any(f.endswith(('.test.ts', '.spec.ts', 'test.py')) for f in files):
            return "testing"
        elif any(f.endswith(('.css', '.scss', '.html')) for f in files):
            return "ui"
        elif "fix" in msg or "bug" in msg:
            return "bugfix"
        elif "feature" in msg:
            return "feature"
        elif "refactor" in msg:
            return "refactor"
        else:
            return "other"
```

### 3. Enhanced Vector Storage (`storage_service.py`)
```python
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from models import ProgressEntry, SearchQuery
from typing import List
import json

class ProgressStorage:
    def __init__(self, vector_store_path: str):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        self.vector_store_path = vector_store_path
        self.vector_store = None
        self._initialize_store()
    
    def _initialize_store(self):
        """Initialize or load existing vector store"""
        try:
            self.vector_store = FAISS.load_local(
                self.vector_store_path, 
                self.embeddings
            )
        except:
            self.vector_store = FAISS.from_texts(
                ["initialization"], 
                self.embeddings
            )
    
    def add_entry(self, entry: ProgressEntry):
        """Add a progress entry to the vector store"""
        # Create rich text representation of the entry
        text = f"""
        Title: {entry.title}
        Date: {entry.date}
        Category: {entry.category}
        Tags: {', '.join(entry.tags)}
        Impact: {entry.impact_level}
        
        Description:
        {entry.description}
        
        Changes:
        {self._format_changes(entry.changes)}
        """
        
        # Add to vector store with metadata
        metadata = {
            "id": entry.id,
            "date": entry.date.isoformat(),
            "category": entry.category,
            "tags": json.dumps(entry.tags),
            "impact_level": entry.impact_level
        }
        
        self.vector_store.add_texts([text], metadatas=[metadata])
        self.vector_store.save_local(self.vector_store_path)
    
    def search(self, query: SearchQuery, limit: int = 5) -> List[ProgressEntry]:
        """Search for progress entries"""
        # Create filter based on query parameters
        filter_dict = {}
        if query.categories:
            filter_dict["category"] = {"$in": query.categories}
        if query.tags:
            filter_dict["tags"] = {"$in": query.tags}
        
        # Perform search
        results = self.vector_store.similarity_search_with_score(
            query.query,
            k=limit,
            filter=filter_dict if filter_dict else None
        )
        
        # Convert results back to ProgressEntry objects
        entries = []
        for doc, score in results:
            metadata = doc.metadata
            entry = ProgressEntry(
                id=metadata["id"],
                date=datetime.fromisoformat(metadata["date"]),
                title=doc.page_content.split("\n")[1].replace("Title: ", "").strip(),
                description=self._extract_description(doc.page_content),
                category=metadata["category"],
                tags=json.loads(metadata["tags"]),
                impact_level=metadata["impact_level"],
                changes=[]  # Changes would need to be stored/retrieved separately
            )
            entries.append(entry)
        
        return entries
    
    def _format_changes(self, changes: List[CodeChange]) -> str:
        """Format code changes for text representation"""
        return "\n".join(
            f"- [{change.timestamp}] {change.description} "
            f"(Files: {', '.join(change.files_changed)})"
            for change in changes
        )
    
    def _extract_description(self, text: str) -> str:
        """Extract description from document text"""
        start = text.find("Description:") + 12
        end = text.find("Changes:")
        return text[start:end].strip()
```

### 4. Progress API (`main.py`)
```python
from fastapi import FastAPI, HTTPException
from models import ProgressEntry, SearchQuery
from progress_tracker import ProgressTracker
from storage_service import ProgressStorage
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Initialize services
tracker = ProgressTracker(os.getenv("CODE_REPO_PATH"))
storage = ProgressStorage(os.getenv("VECTOR_DB_PATH"))

@app.post("/progress")
async def add_progress(entry: ProgressEntry):
    """Add a new progress entry"""
    try:
        storage.add_entry(entry)
        return {"message": "Progress entry added successfully", "id": entry.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_progress(query: SearchQuery):
    """Search progress entries"""
    try:
        results = storage.search(query)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sync")
async def sync_from_git():
    """Sync recent changes from git"""
    try:
        changes = tracker.get_recent_changes(since=datetime.now().replace(hour=0, minute=0))
        # Convert changes to progress entries and store
        for change in changes:
            entry = ProgressEntry(
                id=change.id,
                date=change.timestamp,
                title=f"Code changes: {change.description.split('\n')[0]}",
                description=change.description,
                category=change.category,
                changes=[change],
                tags=[change.category],
                impact_level="minor"
            )
            storage.add_entry(entry)
        return {"message": f"Synced {len(changes)} changes"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

## Key Features for Code Progress Tracking

1. **Git Integration**
   - Automatic tracking of code changes
   - Commit categorization
   - File change analysis

2. **Progress Categorization**
   - Automatic categorization of changes
   - Impact level assessment
   - Tag-based organization

3. **Rich Search Capabilities**
   - Semantic search using embeddings
   - Category and tag filtering
   - Date range filtering

4. **Structured Progress Tracking**
   - Detailed progress entries
   - Change tracking
   - Metadata storage

## Usage Examples

1. **Add Progress Entry**
```bash
curl -X POST "http://localhost:8000/progress" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Implemented form validation",
       "description": "Added comprehensive form validation...",
       "category": "feature",
       "tags": ["forms", "validation"],
       "impact_level": "major"
     }'
```

2. **Search Progress**
```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "form validation improvements",
       "categories": ["feature", "bugfix"],
       "tags": ["forms"]
     }'
```

3. **Sync from Git**
```bash
curl -X GET "http://localhost:8000/sync"
```

## Next Steps

1. **Enhanced Analysis**
   - Code complexity metrics
   - Impact analysis
   - Dependency tracking

2. **Integration Features**
   - CI/CD pipeline integration
   - Issue tracker integration
   - Documentation generation

3. **Advanced Search**
   - Code snippet search
   - Similar change detection
   - Progress pattern analysis

## Frontend Development

1. **User Interface Components**
   - Modern, responsive dashboard layout
   - Progress entry management interface
   - Code change visualization
   - Advanced search interface
   - Real-time updates and notifications

2. **Key Features**
   ```typescript
   // Example frontend component structure
   interface ProgressDashboard {
     components: {
       entryList: ProgressEntryList;
       searchBar: AdvancedSearch;
       visualizations: ProgressCharts;
       filters: FilterPanel;
     }
   }
   ```

## Visualization Tools

1. **Progress Analytics Dashboard**
   - Commit frequency charts
   - Category distribution analysis
   - Impact level metrics
   - Code change trends

2. **Implementation Example**
   ```javascript
   // Example Chart.js implementation
   const commitChart = new Chart(ctx, {
     type: 'line',
     data: {
       datasets: [{
         label: 'Commits per Category',
         data: commitData
       }]
     }
   });
   ```

## Enhanced Search and Analysis

1. **Code Snippet Search**
   - Semantic code search
   - Pattern matching
   - Context-aware results
   - Syntax highlighting

2. **Impact Analysis Tools**
   - Code complexity metrics
   - Dependency graph visualization
   - Change impact assessment
   ```python
   class ImpactAnalyzer:
       def analyze_complexity(self, code_changes: List[CodeChange]) -> Dict:
           # Implement complexity analysis
           pass

       def assess_dependencies(self, changes: List[str]) -> Graph:
           # Generate dependency graph
           pass
   ```

## Scalability and Performance

1. **Vector Database Optimization**
   - Indexing strategies
   - Batch processing
   - Efficient querying patterns
   ```python
   class OptimizedStorage(ProgressStorage):
       def __init__(self, vector_store_path: str):
           super().__init__(vector_store_path)
           self.cache = LRUCache(maxsize=1000)
           self.batch_size = 100
   ```

2. **Caching Implementation**
   - LRU cache for frequent queries
   - Result set caching
   - Metadata caching

## DevOps Integration

1. **CI/CD Pipeline Integration**
   ```yaml
   # Example GitHub Actions workflow
   name: Progress Tracking
   on: [push, pull_request]
   jobs:
     track-progress:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Track Changes
           run: |
             curl -X POST ${{ secrets.PROGRESS_API }}/sync
   ```

2. **Issue Tracker Integration**
   - Automatic linking with Jira/GitHub Issues
   - Progress synchronization
   - Bidirectional updates

## Getting Started with Frontend

1. **Setup Frontend Development**
   ```bash
   # Install frontend dependencies
   npm install @material-ui/core chart.js @monaco-editor/react
   
   # Start development server
   npm run dev
   ```

2. **Configure API Integration**
   ```typescript
   // api.config.ts
   export const API_CONFIG = {
     baseUrl: process.env.API_URL || 'http://localhost:8000',
     endpoints: {
       progress: '/progress',
       search: '/search',
       sync: '/sync'
     }
   };
   ```
