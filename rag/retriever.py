import time
from dataclasses import dataclass, field
from loguru import logger
from rag.embedder import Embedder
from rag.vector_store import VectorStore

@dataclass
class RetrievalContext:
    chunks: list[str]
    citations: list[str]
    combined_context: str
    sources_used: list[str]
    retrieval_time_ms: float

class SarabhaiRetriever:
    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        
    def retrieve(self, query: str, n_results: int = 5, doc_type_filter: str = None, timeline_year: int = None) -> RetrievalContext:
        """Retrieve relevant chunks for a query, applying filters and formatting context."""
        start_time = time.time()
        logger.info(f"Retrieving for query: '{query}'")
        
        # 1. Embed query
        query_emb = self.embedder.embed_query(query)
        
        # 2. Filters
        filters = {}
        if doc_type_filter:
            filters["doc_type"] = doc_type_filter
            
        # 3. Search
        raw_results = self.vector_store.search(query_emb, n_results=n_results*2, filters=filters)
        
        # 4. Post-filter by timeline_year if needed
        filtered_results = []
        for r in raw_results:
            if timeline_year:
                date_str = r.metadata.get("date_approximate", "unknown")
                if date_str != "unknown":
                    try:
                        if int(date_str) > timeline_year:
                            continue # Skip future docs
                    except ValueError:
                        pass
            filtered_results.append(r)
            
        # 5. Deduplicate by source_file (max 2 per source)
        source_counts = {}
        final_results = []
        for r in filtered_results:
            source = r.metadata.get("source_file", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
            if source_counts[source] <= 2:
                final_results.append(r)
            if len(final_results) >= n_results:
                break
                
        # 6. Format RetrievalContext
        chunks = [r.text for r in final_results]
        citations = list(set([r.citation_text for r in final_results]))
        combined_context = "\n\n---\n\n".join(chunks)
        sources_used = list(set([r.metadata.get("source_file", "unknown") for r in final_results]))
        
        end_time = time.time()
        retrieval_time_ms = (end_time - start_time) * 1000
        
        return RetrievalContext(
            chunks=chunks,
            citations=citations,
            combined_context=combined_context,
            sources_used=sources_used,
            retrieval_time_ms=retrieval_time_ms
        )

    def retrieve_for_topic(self, topic: str) -> RetrievalContext:
        """Broad topic retrieval for Mission Planning Mode."""
        start_time = time.time()
        results = self.vector_store.search_by_topic(topic, n_results=10)
        
        chunks = [r.text for r in results]
        citations = list(set([r.citation_text for r in results]))
        combined_context = "\n\n---\n\n".join(chunks)
        sources_used = list(set([r.metadata.get("source_file", "unknown") for r in results]))
        
        retrieval_time_ms = (time.time() - start_time) * 1000
        
        return RetrievalContext(
            chunks=chunks,
            citations=citations,
            combined_context=combined_context,
            sources_used=sources_used,
            retrieval_time_ms=retrieval_time_ms
        )
