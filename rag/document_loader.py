import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from loguru import logger
import fitz  # PyMuPDF

@dataclass
class RawDocument:
    text: str
    metadata: dict = field(default_factory=dict)

class DocumentLoader:
    def load_pdf(self, file_path: str) -> list[RawDocument]:
        """Use PyMuPDF (fitz) to extract text page by page.
        Clean: strip repeated whitespace, remove page number artifacts,
        fix hyphenated line breaks. Return list with text, page_num, file_path."""
        logger.info(f"Loading PDF: {file_path}")
        docs = []
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # Cleaning
                text = re.sub(r'\s+', ' ', text)  # Strip repeated whitespace
                text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE) # Remove isolated numbers (potential page numbers)
                text = re.sub(r'-\s+', '', text) # Fix hyphenated line breaks
                text = text.strip()
                
                if text:
                    docs.append(RawDocument(text=text, metadata={"page_num": page_num + 1, "source_file": os.path.basename(file_path)}))
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
        return docs
        
    def load_txt(self, file_path: str) -> list[RawDocument]:
        """Read plain text. Split into paragraphs at double newlines."""
        logger.info(f"Loading TXT: {file_path}")
        docs = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            for i, p in enumerate(paragraphs):
                docs.append(RawDocument(text=p, metadata={"paragraph_num": i + 1, "source_file": os.path.basename(file_path)}))
        except Exception as e:
            logger.error(f"Error loading TXT {file_path}: {e}")
        return docs
        
    def load_json(self, file_path: str) -> list[RawDocument]:
        """Read JSON array of {text, source, date}."""
        logger.info(f"Loading JSON: {file_path}")
        docs = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    text = item.get("text", "").strip()
                    if text:
                        metadata = {k: v for k, v in item.items() if k != "text"}
                        metadata["source_file"] = os.path.basename(file_path)
                        docs.append(RawDocument(text=text, metadata=metadata))
        except Exception as e:
            logger.error(f"Error loading JSON {file_path}: {e}")
        return docs
        
    def load_directory(self, dir_path: str, doc_type: str) -> list[RawDocument]:
        """Walk all files in dir, call appropriate loader.
        doc_type: speech, paper, interview, book, institutional."""
        logger.info(f"Loading directory: {dir_path} (doc_type: {doc_type})")
        all_docs = []
        path = Path(dir_path)
        if not path.exists() or not path.is_dir():
            logger.warning(f"Directory {dir_path} does not exist.")
            return all_docs
            
        for file_path in path.rglob('*'):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                docs = []
                if ext == '.pdf':
                    docs = self.load_pdf(str(file_path))
                elif ext == '.txt':
                    docs = self.load_txt(str(file_path))
                elif ext == '.json':
                    docs = self.load_json(str(file_path))
                else:
                    logger.debug(f"Skipping unsupported file type: {file_path}")
                
                for doc in docs:
                    doc.metadata["doc_type"] = doc_type
                all_docs.extend(docs)
        return all_docs
        
    @staticmethod
    def detect_date(text: str) -> str:
        """Use regex to extract years. Return 'unknown' if none found."""
        matches = re.findall(r'\b(19\d{2}|20\d{2})\b', text)
        if matches:
            return matches[0] # Return the first found year
        return "unknown"
