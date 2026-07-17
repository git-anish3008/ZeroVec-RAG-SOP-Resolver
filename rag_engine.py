import os
import lancedb
from docling.document_converter import DocumentConverter
from docling.chunking import HierarchicalChunker

# Configuration constants
DB_PATH = "./.lancedb_vectorless"
TABLE_NAME = "office_docs"

def process_and_store_documents(file_paths):
    """
    Parses a list of documents, chunks them hierarchically, and stores them in LanceDB.
    Appends to existing data instead of overwriting.
    """
    if not file_paths:
        return False, "No files provided."

    print(f"Processing {len(file_paths)} document(s)...")
    converter = DocumentConverter()
    chunker = HierarchicalChunker()

    all_chunks = []

    for file_path in file_paths:
        print(f" -> Parsing: {file_path}")
        try:
            # Parse the document
            result = converter.convert(file_path)
            doc = result.document

            # Chunk the document hierarchically
            chunks = list(chunker.chunk(doc))

            # Extract filename safely
            safe_filename = os.path.basename(file_path)

            # Format chunks into dictionaries
            for chunk in chunks:
                if chunk.meta.headings:
                    toc_path = " > ".join(chunk.meta.headings)
                else:
                    toc_path = "Document Root"

                all_chunks.append({
                    "text": chunk.text,
                    "toc_section": toc_path,
                    "file_name": safe_filename
                })
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue

    if not all_chunks:
        return False, "No readable text extracted from documents."

    print(f"Successfully extracted {len(all_chunks)} chunks. Storing in database...")

    # Database Logic
    db = lancedb.connect(DB_PATH)

    # The Overwrite Fix: Check if table exists
    if TABLE_NAME in db.table_names():
        table = db.open_table(TABLE_NAME)
        table.add(all_chunks)  # Append new data!
        print(" -> Appended chunks to existing table.")
    else:
        table = db.create_table(TABLE_NAME, data=all_chunks)
        print(" -> Created new table for documents.")

    # Rebuild the BM25 Index to include the new data
    print(" -> Building/Updating BM25 Full-Text Search Index...")
    table.create_fts_index("text", replace=True)

    return True, f"Successfully processed and indexed {len(file_paths)} document(s)."


def query_knowledge_base(user_question, limit=4):
    """
    Searches the LanceDB index using BM25 and returns a formatted context string.
    """
    db = lancedb.connect(DB_PATH)

    # Failsafe if the user asks a question before uploading anything
    if TABLE_NAME not in db.table_names():
        return "ERROR_EMPTY_DB"

    table = db.open_table(TABLE_NAME)

    # Perform the Vectorless Search
    results = table.search(user_question, query_type="fts").limit(limit).to_list()

    if not results:
        return ""

    # Format the retrieved chunks into a clean context block
    context_string = ""
    for res in results:
        context_string += f"--- Source: {res['file_name']} | Section: {res['toc_section']} ---\n"
        context_string += f"{res['text']}\n\n"

    return context_string
