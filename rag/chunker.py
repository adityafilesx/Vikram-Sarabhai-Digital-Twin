import os
import uuid
from dataclasses import dataclass, field
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

@dataclass
class DocumentChunk:
    chunk_id: str
    text: str
    source_file: str
    doc_type: str
    date_approximate: str
    topic_tags: list[str]
    citation_text: str
    char_start: int
    chunk_index: int

class Chunker:
    TOPIC_KEYWORDS = {
        'space_programme': ['space', 'satellite', 'rocket', 'launch', 'orbit', 'isro', 'incospar', 'thumba'],
        'education': ['education', 'university', 'student', 'teaching', 'learning', 'iim', 'institute'],
        'nuclear_energy': ['nuclear', 'atomic', 'reactor', 'fission', 'energy'],
        'cosmic_rays': ['cosmic', 'rays', 'radiation', 'particle', 'meson'],
        'institution_building': ['institution', 'organization', 'founded', 'established', 'commission'],
        'national_development': ['development', 'nation', 'india', 'planning', 'economy', 'growth'],
        'international_cooperation': ['international', 'cooperation', 'united nations', 'collaboration', 'global'],
        'technology_policy': ['technology', 'policy', 'strategy', 'innovation', 'self-reliance'],
        'physics': ['physics', 'experiment', 'laboratory', 'measurement', 'theory'],
        'management': ['management', 'leadership', 'administration', 'governance'],
    }
    
    def __init__(self):
        load_dotenv()
        chunk_size = int(os.getenv('CHUNK_SIZE', '512'))
        chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '50'))
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=['\n\n', '\n', '. ', ' ', '']
        )
    
    def chunk_document(self, raw_docs: list, source_file: str, doc_type: str) -> list[DocumentChunk]:
        """Takes a list of RawDocument objects, joins text if appropriate, and chunks it."""
        chunks = []
        full_text = " ".join([doc.text for doc in raw_docs])
        
        from rag.document_loader import DocumentLoader
        date_approximate = DocumentLoader.detect_date(full_text)
        
        split_texts = self.splitter.split_text(full_text)
        
        char_start = 0
        for i, text in enumerate(split_texts):
            topic_tags = self.auto_tag_chunk(text)
            date_in_chunk = DocumentLoader.detect_date(text)
            date_to_use = date_in_chunk if date_in_chunk != 'unknown' else date_approximate
            
            citation_text = f"[Sarabhai, {doc_type}, ~{date_to_use}]"
            
            chunk = DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                text=text,
                source_file=source_file,
                doc_type=doc_type,
                date_approximate=date_to_use,
                topic_tags=topic_tags,
                citation_text=citation_text,
                char_start=char_start,
                chunk_index=i
            )
            chunks.append(chunk)
            char_start += len(text) # Approximation, since splitting might drop separators
            
        return chunks
        
    def auto_tag_chunk(self, text: str) -> list[str]:
        """Assign topic tags based on keyword matching."""
        tags = []
        text_lower = text.lower()
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    tags.append(topic)
                    break
        return tags
