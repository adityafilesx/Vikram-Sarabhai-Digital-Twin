import argparse
import time
import os
from loguru import logger
from dotenv import load_dotenv

from rag.document_loader import DocumentLoader
from rag.chunker import Chunker
from rag.embedder import Embedder
from rag.vector_store import VectorStore

def run_pipeline(corpus_dir: str = None, reset: bool = False):
    load_dotenv()
    
    start_time = time.time()
    logger.info("Starting RAG ingestion pipeline")
    
    base_corpus_dir = corpus_dir or os.getenv('CORPUS_DIR', './data/corpus')
    
    vector_store = VectorStore()
    if reset:
        logger.info("Resetting collection")
        vector_store.delete_collection()
        # Re-initialize after deletion to recreate
        vector_store = VectorStore()
        
    loader = DocumentLoader()
    chunker = Chunker()
    embedder = Embedder()
    
    doc_types = ["speeches", "papers", "interviews", "institutional"]
    
    all_chunks = []
    
    for doc_type in doc_types:
        dir_path = os.path.join(base_corpus_dir, doc_type)
        if not os.path.exists(dir_path):
            logger.warning(f"Directory {dir_path} not found. Skipping.")
            continue
            
        raw_docs = loader.load_directory(dir_path, doc_type)
        if not raw_docs:
            continue
            
        # Group raw docs by source_file to chunk them together
        from collections import defaultdict
        docs_by_source = defaultdict(list)
        for doc in raw_docs:
            source = doc.metadata.get("source_file", "unknown")
            docs_by_source[source].append(doc)
            
        for source, docs in docs_by_source.items():
            chunks = chunker.chunk_document(docs, source, doc_type)
            all_chunks.extend(chunks)
            
    logger.info(f"Total chunks created: {len(all_chunks)}")
    
    if all_chunks:
        texts_to_embed = [chunk.text for chunk in all_chunks]
        embeddings = embedder.embed_batch(texts_to_embed)
        
        vector_store.add_chunks(all_chunks, embeddings)
        
    end_time = time.time()
    stats = vector_store.get_collection_stats()
    
    logger.info(f"Pipeline completed in {end_time - start_time:.2f}s")
    logger.info(f"Collection stats: {stats}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest Sarabhai corpus into ChromaDB')
    parser.add_argument('--reset', action='store_true', help='Delete and rebuild collection')
    parser.add_argument('--corpus-dir', default=None, help='Override corpus directory')
    args = parser.parse_args()
    
    run_pipeline(args.corpus_dir, args.reset)
