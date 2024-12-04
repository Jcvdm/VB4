from langchain.vectorstores import Qdrant
from langchain.embeddings import HuggingFaceEmbeddings
from models import ProgressEntry, SearchQuery
from typing import List
import json
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

class ProgressStorage:
    def __init__(self, vector_store_path: str):
        """Initialize the vector storage with Qdrant"""
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        self.collection_name = "progress_entries"
        self.client = QdrantClient("localhost", port=6333)
        self._initialize_store()
    
    def _initialize_store(self):
        """Initialize or get existing Qdrant collection"""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embeddings.client.get_sentence_embedding_dimension(),
                    distance=Distance.COSINE
                )
            )
        
        self.vector_store = Qdrant(
            client=self.client,
            collection_name=self.collection_name,
            embeddings=self.embeddings
        )
    
    def _format_changes(self, changes: List[dict]) -> str:
        """Format code changes for storage"""
        formatted = []
        for change in changes:
            formatted.append(
                f"- {change.description}\n"
                f"  Files: {', '.join(change.files_changed)}\n"
                f"  Category: {change.category}\n"
                f"  Impact: {change.metadata.get('lines_added', 0)} additions, "
                f"{change.metadata.get('lines_deleted', 0)} deletions"
            )
        return "\n".join(formatted)
    
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
                description=doc.page_content,
                category=metadata["category"],
                tags=json.loads(metadata["tags"]),
                impact_level=metadata["impact_level"],
                changes=[]  # Note: Original changes are summarized in description
            )
            entries.append(entry)
        
        return entries
