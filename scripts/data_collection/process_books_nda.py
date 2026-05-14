#!/usr/bin/env python3
"""
NDA-Compliant Book Processor for Dave
Processes licensed security books (PDF/EPUB/MOBI) to extract reporting-relevant sections.
ZERO DISCLOSURE: Never logs filenames, paths, or content details.
Outputs anonymous training pairs to data/processed/books/
"""

import os
import re
import json
import sys
import subprocess
from pathlib import Path

# --- GET BOOKS DIRECTORY FROM COMMAND LINE ARGUMENT ---
if len(sys.argv) < 2:
    print("Usage: python3 process_books_nda.py <path_to_licensed_books_directory>")
    print("Example: python3 process_books_nda.py /home/akclark/licensed_security_books")
    sys.exit(1)

BOOKS_DIR = Path(sys.argv[1])
OUTPUT_DIR = Path("/home/akclark/Dave_repo/data/processed/books")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- TEXT EXTRACTION FUNCTIONS ---

def extract_text_from_pdf(file_path):
    """Extract text from PDF using pdftotext (from poppler-utils)"""
    try:
        # Use pdftotext with layout preservation to maintain structure
        result = subprocess.run(
            ['pdftotext', '-layout', str(file_path), '-'],
            capture_output=True, text=True, check=True, timeout=30
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        # Silently skip problematic files to avoid logging details
        return ""
    except FileNotFoundError:
        print("ERROR: pdftotext not found. Install poppler-utils: sudo apt install poppler-utils")
        return ""
    except Exception:
        return ""

def extract_text_from_epub(file_path):
    """Extract text from EPUB using ebooklib"""
    try:
        # This requires ebooklib and beautifulsoup4
        # Install via: pip install ebooklib beautifulsoup4 lxml
        from ebooklib import epub
        from bs4 import BeautifulSoup
        
        book = epub.read_epub(str(file_path))
        text = ""
        for item in book.get_items():
            if item.get_type() == epub.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text += soup.get_text() + "\n"
        return text
    except ImportError:
        # Silently skip if dependencies not installed
        return ""
    except Exception:
        return ""

def extract_text_from_mobi(file_path):
    """Extract text from MOBI by converting to EPUB first (requires calibre)"""
    try:
        # This requires calibre: sudo apt install calibre
        import tempfile
        import os
        
        # Create a temporary EPUB file
        with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp_epub:
            epub_path = tmp_epub.name
        
        # Convert MOBI to EPUB using ebook-convert (from calibre)
        subprocess.run(
            ['ebook-convert', str(file_path), epub_path],
            capture_output=True, check=True, timeout=60
        )
        
        # Extract text from the EPUB
        text = extract_text_from_epub(Path(epub_path))
        
        # Clean up temporary file
        try:
            os.unlink(epub_path)
        except:
            pass
            
        return text
    except (ImportError, FileNotFoundError, subprocess.CalledProcessError):
        # Silently skip if dependencies not installed or conversion fails
        return ""
    except Exception:
        return ""

# --- PROCESSING LOGIC (NDA-SAFE) ---

def is_reporting_section(text_chunk):
    """Heuristic to identify reporting-relevant content (findings, remediation, methodology)"""
    reporting_indicators = [
        r'(?i)finding[s]?', r'(?i)remediation', r'(?i)methodology',
        r'(?i)recommendation', r'(?i)mitigation', r'(?i)vulnerability',
        r'(?i)risk\s+assessment', r'(?i)evidence', r'(?i)proof\s+of\s+concept',
        r'(?i)scan\s+results', r'(?i)exploitation\s+details',
        r'(?i)business\s+impact', r'(?i)technical\s+detail'
    ]
    pattern = re.compile('|'.join(reporting_indicators))
    return bool(pattern.search(text_chunk))

def chunk_text(text, max_tokens=400):
    """Simple text chunking by sentences (user should refine as needed)"""
    sentences = re.split(r'[.!?]+', text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        # Rough token estimate: 1.3 tokens per word
        estimated_tokens = len(sentence.split()) * 1.3
        if current_length + estimated_tokens > max_tokens and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_length = estimated_tokens
        else:
            current_chunk.append(sentence)
            current_length += estimated_tokens
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

def generate_training_pair(chunk):
    """Convert a reporting chunk into a prompt/completion pair for Dave"""
    # This is where you'd implement your specific prompt engineering
    # Example structure - user must customize based on their books' style
    prompt = f"Technical finding: [Extract key vulnerability/finding from context]"
    completion = f"Executive summary: [Write APA/(ISC)²-aligned summary based on chunk]"
    # User MUST replace the bracketed placeholders with actual logic
    # that processes 'chunk' to generate meaningful prompt/completion
    return {"prompt": prompt, "completion": completion}

def main():
    print("Starting NDA-compliant book processing...")
    print(f"Source directory: {BOOKS_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("WARNING: User must verify BOOKS_DIR is set to their licensed collection!")
    
    if not BOOKS_DIR.exists():
        print(f"ERROR: Directory {BOOKS_DIR} does not exist")
        sys.exit(1)
    
    processed_count = 0
    total_chunks = 0
    error_count = 0
    
    # Process all supported formats
    for ext in ['pdf', 'epub', 'mobi']:
        for file_path in BOOKS_DIR.rglob(f"*.{ext}"):
            try:
                # Extract text
                if ext == 'pdf':
                    text = extract_text_from_pdf(file_path)
                elif ext == 'epub':
                    text = extract_text_from_epub(file_path)
                elif ext == 'mobi':
                    text = extract_text_from_mobi(file_path)
                else:
                    continue
                
                if not text.strip():
                    # Silently skip empty files to avoid logging details
                    continue
                
                # Chunk and filter for reporting sections
                chunks = chunk_text(text)
                reporting_chunks = [c for c in chunks if is_reporting_section(c)]
                
                # Generate training pairs
                for chunk in reporting_chunks:
                    pair = generate_training_pair(chunk)
                    # Output as JSONL
                    output_file = OUTPUT_DIR / "books_training.jsonl"
                    with open(output_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(pair) + '\n')
                    total_chunks += 1
                
                processed_count += 1
                # NDA-SAFE: Never log filename or path
                if processed_count % 10 == 0:
                    print(f"Processed {processed_count} books... ({total_chunks} reporting chunks)")
                    
            except Exception as e:
                # NDA-SAFE: Log only error type, not file details
                error_count += 1
                if error_count <= 5:  # Only show first few errors to avoid spam
                    print(f"Error processing book: {type(e).__name__}")
                continue
    
    print(f"\nProcessing complete.")
    print(f"Books processed: {processed_count}")
    print(f"Reporting chunks extracted: {total_chunks}")
    if error_count > 0:
        print(f"Errors encountered: {error_count} (see above for first few)")
    print(f"Training data saved to: {OUTPUT_DIR / 'books_training.jsonl'}")

if __name__ == "__main__":
    main()
