import pytest
from rag.document_loader import DocumentLoader, RawDocument
from rag.chunker import Chunker

def test_document_loader_detect_date():
    loader = DocumentLoader()
    text = "This paper was published in 1965 at the conference."
    date = loader.detect_date(text)
    assert date == "1965"
    
    text_no_date = "This is a random text."
    assert loader.detect_date(text_no_date) == "unknown"

def test_chunker():
    chunker = Chunker()
    raw_docs = [RawDocument(text="This is a test document. " * 50, metadata={"source_file": "test.txt", "date_approximate": "1962"})]
    chunks = chunker.chunk_document(raw_docs, source_file="test.txt", doc_type="papers")
    
    assert len(chunks) > 0
    assert chunks[0].source_file == "test.txt"
    assert chunks[0].doc_type == "papers"

def test_auto_tag_chunk():
    chunker = Chunker()
    tags = chunker.auto_tag_chunk("The space programme in India started with sounding rockets.")
    assert "space_programme" in tags
