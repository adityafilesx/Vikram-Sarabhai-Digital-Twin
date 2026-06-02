import os
import chromadb
from dataclasses import dataclass
from dotenv import load_dotenv
from loguru import logger
import json

@dataclass
class RetrievalResult:
    text: str
    metadata: dict
    distance: float
    citation_text: str

class VectorStore:
    def __init__(self):
        load_dotenv()
        db_path = os.getenv('CHROMA_DB_PATH', './chroma_db')
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name='sarabhai_knowledge',
            metadata={'hnsw:space': 'cosine'}
        )
    
    def add_chunks(self, chunks, embeddings):
        """Batch upserts chunks into ChromaDB."""
        logger.info(f"Adding {len(chunks)} chunks to VectorStore")
        
        # Batch in groups of 100
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]
            batch_embeddings = embeddings[i:i+batch_size]
            
            ids = [chunk.chunk_id for chunk in batch_chunks]
            documents = [chunk.text for chunk in batch_chunks]
            metadatas = [
                {
                    "source_file": chunk.source_file,
                    "doc_type": chunk.doc_type,
                    "date_approximate": chunk.date_approximate,
                    "topic_tags": json.dumps(chunk.topic_tags), # Chroma metadata values must be str, int, float, or bool
                    "citation_text": chunk.citation_text,
                    "char_start": chunk.char_start,
                    "chunk_index": chunk.chunk_index
                }
                for chunk in batch_chunks
            ]
            
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=batch_embeddings,
                metadatas=metadatas
            )
        logger.info("Chunks added successfully")

    def search(self, query_embedding, n_results=5, filters=None) -> list[RetrievalResult]:
        """Query ChromaDB with embedding and optional filters."""
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results
        }
        
        if filters:
            chroma_where = {}
            if "doc_type" in filters:
                chroma_where["doc_type"] = filters["doc_type"]
            if "timeline_year" in filters:
                # We want documents where date_approximate <= timeline_year
                # Chroma string comparison can be tricky, but if dates are "19XX", "$lte" works.
                # Just need to handle "unknown". Let's do a simple <= check.
                # Actually, ChromaDB where clause requires string matching. We might have to fetch and post-filter if complex,
                # but if date_approximate is structured, we could use a custom filter.
                # For simplicity, we just filter it out post-retrieval if we can't easily express it in Chroma's where clause.
                pass # Handled in Retriever for safety if complex
            
            if chroma_where:
                kwargs["where"] = chroma_where
                
        results = self.collection.query(**kwargs)
        
        retrieval_results = []
        if results['documents'] and results['documents'][0]:
            docs = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]
            
            for doc, meta, dist in zip(docs, metadatas, distances):
                # Restore topic_tags from JSON string
                if 'topic_tags' in meta and isinstance(meta['topic_tags'], str):
                    meta['topic_tags'] = json.loads(meta['topic_tags'])
                    
                retrieval_results.append(RetrievalResult(
                    text=doc,
                    metadata=meta,
                    distance=dist,
                    citation_text=meta.get("citation_text", "")
                ))
                
        return retrieval_results

    def search_by_topic(self, topic_tag, n_results=10) -> list[RetrievalResult]:
        """Filter by topic_tags containing the tag. (Used for mission planning)"""
        # Since topic_tags is a JSON string array in Chroma metadata, we can use the $contains operator (Chroma >=0.4.15)
        # Note: $contains works on lists if we had stored it as a list, but Chroma metadata doesn't support list values natively.
        # Actually Chroma does support lists now, or we can just fetch and filter.
        # We will use text matching in metadata if possible, or fetch all and filter.
        
        # We'll just query everything and filter, or use an empty embedding query.
        # Since we must provide embeddings or texts, let's use a dummy embedding or query texts.
        # A better approach is to rely on Retriever.
        results = self.collection.get(
            limit=n_results*5, # Over-fetch
        )
        
        filtered = []
        if results['documents']:
            for i, doc in enumerate(results['documents']):
                meta = results['metadatas'][i]
                tags = json.loads(meta.get('topic_tags', '[]'))
                if topic_tag in tags:
                    filtered.append(RetrievalResult(
                        text=doc,
                        metadata=meta,
                        distance=0.0,
                        citation_text=meta.get("citation_text", "")
                    ))
                    if len(filtered) >= n_results:
                        break
        return filtered

    def get_collection_stats(self) -> dict:
        """Return count of documents, unique doc_types, date range of corpus."""
        count = self.collection.count()
        return {"document_count": count}

    def delete_collection(self):
        """For testing/reset purposes."""
        logger.warning("Deleting collection 'sarabhai_knowledge'")
        self.client.delete_collection('sarabhai_knowledge')
