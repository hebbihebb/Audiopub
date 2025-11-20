import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Dict

class EpubParser:
    def __init__(self, epub_path: str):
        self.epub_path = epub_path
        try:
            self.book = epub.read_epub(epub_path)
        except Exception as e:
            raise ValueError(f"Could not read EPUB file: {e}")

    def extract_text(self) -> List[Dict]:
        """
        Extracts text from the EPUB, returning a list of chapters/sections.
        Each item is a dict: {'title': str, 'content': str, 'id': str}
        """
        chapters = []
        # Iterate over items in the spine to maintain order
        for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
             # We might want to check spine order if needed, but get_items_of_type usually returns all.
             # Better: loop through spine.
             pass

        # Correct way to iterate in reading order
        for item_id in self.book.spine:
            # item_id is a tuple (id, linear)
            item = self.book.get_item_with_id(item_id[0])
            if not item:
                continue

            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content()
                soup = BeautifulSoup(content, 'html.parser')

                # Extract title if present (h1, h2, or title tag)
                title = ""
                if soup.title:
                    title = soup.title.string
                if not title:
                    header = soup.find(['h1', 'h2', 'h3'])
                    if header:
                        title = header.get_text().strip()

                # Extract text
                # Remove scripts and styles
                for script in soup(["script", "style"]):
                    script.decompose()

                text = soup.get_text(separator=' ')

                # Clean text
                cleaned_text = self._clean_text(text)

                if len(cleaned_text) > 10: # Skip empty or very short sections
                    chapters.append({
                        'title': title or "Untitled Section",
                        'content': cleaned_text,
                        'id': item.get_name()
                    })
        return chapters

    def _clean_text(self, text: str) -> str:
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove page numbers (e.g., "pg 45", "Page 12") - naive regex
        text = re.sub(r'\b(pg|page)\.?\s*\d+\b', '', text, flags=re.IGNORECASE)
        return text

    @staticmethod
    def chunk_text(text: str, min_chunk_size: int = 1000, max_chunk_size: int = 2000) -> List[str]:
        """
        Splits text into chunks of approximately max_chunk_size, breaking on sentence boundaries.
        """
        if not text:
            return []

        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            if current_length + len(sentence) > max_chunk_size and current_length >= min_chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
