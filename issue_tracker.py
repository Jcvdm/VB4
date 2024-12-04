from typing import List, Optional
from datetime import datetime
from github import Github
from models import ProgressEntry

class GitHubIssueTracker:
    def __init__(self, token: str, repo: str):
        """Initialize GitHub issue tracker
        
        Args:
            token (str): GitHub personal access token
            repo (str): Repository in format 'username/repo'
        """
        self.github = Github(token)
        self.repo = self.github.get_repo(repo)

    def create_issue(self, title: str, description: str, labels: List[str]) -> str:
        """Create a new GitHub issue
        
        Args:
            title (str): Issue title
            description (str): Issue description
            labels (List[str]): List of labels to apply
            
        Returns:
            str: Issue number as string
        """
        issue = self.repo.create_issue(
            title=title,
            body=description,
            labels=labels
        )
        return str(issue.number)

    def update_issue(self, issue_id: str, status: str, comment: Optional[str] = None):
        """Update an issue's status and optionally add a comment
        
        Args:
            issue_id (str): Issue number
            status (str): New status (e.g., 'open', 'closed')
            comment (Optional[str]): Optional comment to add
        """
        issue = self.repo.get_issue(int(issue_id))
        if comment:
            issue.create_comment(comment)
        
        if status.lower() == "closed":
            issue.edit(state="closed")
        else:
            issue.edit(state="open")

    def link_to_progress(self, issue_id: str, progress_entry: ProgressEntry):
        """Link a progress entry to an issue by adding a comment
        
        Args:
            issue_id (str): Issue number
            progress_entry (ProgressEntry): Progress entry to link
        """
        issue = self.repo.get_issue(int(issue_id))
        comment = f"""
## Progress Update
- Title: {progress_entry.title}
- Date: {progress_entry.date}
- Category: {progress_entry.category}
- Impact: {progress_entry.impact_level}
- Tags: {', '.join(progress_entry.tags)}

### Description
{progress_entry.description}

### Changes
{self._format_changes(progress_entry.changes)}
        """
        issue.create_comment(comment)

    def _format_changes(self, changes: List[dict]) -> str:
        """Format changes for GitHub markdown
        
        Args:
            changes (List[dict]): List of changes to format
            
        Returns:
            str: Formatted changes in markdown
        """
        formatted = []
        for change in changes:
            formatted.append(
                f"- {change.description}\n"
                f"  - Files: {', '.join(change.files_changed)}\n"
                f"  - Category: {change.category}"
            )
        return "\n".join(formatted)
