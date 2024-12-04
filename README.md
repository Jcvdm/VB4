# Code Progress Tracking System

A system for tracking and searching code development progress using vector embeddings and LLM integration.

## Features

- Track code changes from Git repositories
- Categorize and tag development progress
- Search progress entries using natural language queries
- Vector-based similarity search using FAISS
- REST API and CLI interfaces

## Prerequisites

- Python 3.8+
- Git repository
- OpenAI API key (for future LLM integration)

## Installation

1. Clone the repository and create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```
OPENAI_API_KEY=your_openai_api_key_here
CODE_REPO_PATH=/path/to/your/code/repo
VECTOR_DB_PATH=./vector_store
```

## Usage

### Using the CLI

1. Add a progress entry:
```bash
python cli.py add -t "New Feature" -d "Implemented user authentication" -c feature -g auth -g security -i major
```

2. Search progress entries:
```bash
python cli.py search -q "authentication implementation" -c feature -t auth
```

### Using the API

1. Start the API server:
```bash
uvicorn main:app --reload
```

2. Access the API documentation at `http://localhost:8000/docs`

### API Endpoints

- POST `/progress/`: Create a new progress entry
- POST `/search/`: Search progress entries
- GET `/categories/`: Get available categories
- GET `/health/`: Check service health

## Project Structure

- `models.py`: Data models for the application
- `progress_tracker.py`: Git repository tracking and commit categorization
- `storage_service.py`: Vector storage and search functionality
- `main.py`: FastAPI server implementation
- `cli.py`: Command-line interface
- `.env`: Configuration file

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
