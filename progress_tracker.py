from git import Repo
import os
from datetime import datetime
from models import CodeChange, ProgressEntry
from typing import List

class ProgressTracker:
    def __init__(self, repo_path: str):
        """Initialize the progress tracker with a git repository path"""
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
            
    def create_progress_entry(self, title: str, description: str, category: str, 
                            tags: List[str] = None, impact_level: str = "minor") -> ProgressEntry:
        """Create a progress entry from recent changes"""
        recent_changes = self.get_recent_changes(
            since=datetime.now().replace(hour=0, minute=0)
        )
        
        return ProgressEntry(
            id=str(datetime.now().timestamp()),
            date=datetime.now(),
            title=title,
            description=description,
            changes=recent_changes,
            category=category,
            tags=tags or [],
            impact_level=impact_level
        )
