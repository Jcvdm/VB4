import click
from dotenv import load_dotenv
import os
from progress_tracker import ProgressTracker
from storage_service import ProgressStorage
from models import SearchQuery
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize services
tracker = ProgressTracker(os.getenv("CODE_REPO_PATH"))
storage = ProgressStorage(os.getenv("VECTOR_DB_PATH"))

@click.group()
def cli():
    """Code Progress Tracking CLI"""
    pass

@cli.command()
@click.option('--title', '-t', required=True, help='Title of the progress entry')
@click.option('--description', '-d', required=True, help='Description of the progress')
@click.option('--category', '-c', required=True, help='Category of the progress')
@click.option('--tags', '-g', multiple=True, help='Tags for the progress entry')
@click.option('--impact', '-i', default='minor', help='Impact level (minor/major/critical)')
def add(title, description, category, tags, impact):
    """Add a new progress entry"""
    try:
        entry = tracker.create_progress_entry(
            title=title,
            description=description,
            category=category,
            tags=list(tags),
            impact_level=impact
        )
        storage.add_entry(entry)
        click.echo(f"Successfully added progress entry: {title}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
@click.option('--query', '-q', required=True, help='Search query')
@click.option('--category', '-c', multiple=True, help='Filter by categories')
@click.option('--tags', '-t', multiple=True, help='Filter by tags')
@click.option('--limit', '-l', default=5, help='Maximum number of results')
def search(query, category, tags, limit):
    """Search progress entries"""
    try:
        search_query = SearchQuery(
            query=query,
            categories=list(category) if category else None,
            tags=list(tags) if tags else None
        )
        results = storage.search(search_query, limit=limit)
        
        if not results:
            click.echo("No results found.")
            return
            
        for entry in results:
            click.echo("-" * 50)
            click.echo(f"Title: {entry.title}")
            click.echo(f"Date: {entry.date}")
            click.echo(f"Category: {entry.category}")
            click.echo(f"Tags: {', '.join(entry.tags)}")
            click.echo(f"Impact: {entry.impact_level}")
            click.echo("\nDescription:")
            click.echo(entry.description)
            click.echo("-" * 50)
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

if __name__ == '__main__':
    cli()
