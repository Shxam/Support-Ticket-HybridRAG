"""
Indexing module for Hybrid RAG.

Builds BM25 sparse indexes and dense embedding indexes for each domain.
Creates both domain-specific indexes and a global index for company="None" cases.
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from config import (
    DATA_DIR,
    EMBEDDINGS_DIR,
    INDEX_DIR,
    DOMAINS,
    EMBEDDING_MODEL,
    RANDOM_SEED
)


# Set random seed for reproducibility
np.random.seed(RANDOM_SEED)


def load_documents_from_domain(domain: str) -> List[Tuple[str, str]]:
    """
    Load all document texts from a domain directory.
    
    Args:
        domain: Domain name (hackerrank, claude, visa)
        
    Returns:
        List of tuples (document_text, filepath)
    """
    domain_dir = os.path.join(DATA_DIR, domain)
    documents = []
    
    if not os.path.exists(domain_dir):
        print(f"[INDEX] Warning: Domain directory not found: {domain_dir}")
        return documents
    
    for filename in os.listdir(domain_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(domain_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append((content, filepath))
            except Exception as e:
                print(f"[INDEX] Error reading {filepath}: {str(e)}")
    
    return documents


def build_bm25_index(documents: List[str]) -> BM25Okapi:
    """
    Build BM25 sparse index from documents.
    
    Args:
        documents: List of document texts
        
    Returns:
        BM25Okapi index
    """
    # Tokenize documents (simple whitespace tokenization)
    tokenized_docs = [doc.lower().split() for doc in documents]
    
    # Build BM25 index
    bm25 = BM25Okapi(tokenized_docs)
    
    return bm25


def build_embedding_index(documents: List[str], model: SentenceTransformer) -> np.ndarray:
    """
    Build dense embedding index from documents.
    
    Args:
        documents: List of document texts
        model: SentenceTransformer model for encoding
        
    Returns:
        Numpy array of embeddings (num_docs x embedding_dim)
    """
    print(f"[INDEX] Encoding {len(documents)} documents...")
    
    # Encode documents in batches
    embeddings = model.encode(
        documents,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    
    return embeddings


def save_index(index_data: Dict, domain: str):
    """
    Save index data to disk.
    
    Args:
        index_data: Dictionary containing index components
        domain: Domain name for the index
    """
    os.makedirs(INDEX_DIR, exist_ok=True)
    
    # Save BM25 index
    bm25_path = os.path.join(INDEX_DIR, f"{domain}_bm25.pkl")
    with open(bm25_path, 'wb') as f:
        pickle.dump(index_data['bm25'], f)
    
    # Save embeddings
    embeddings_path = os.path.join(EMBEDDINGS_DIR, f"{domain}_embeddings.npy")
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    np.save(embeddings_path, index_data['embeddings'])
    
    # Save document metadata
    metadata_path = os.path.join(INDEX_DIR, f"{domain}_metadata.pkl")
    with open(metadata_path, 'wb') as f:
        pickle.dump(index_data['metadata'], f)
    
    print(f"[INDEX] Saved index for {domain}")


def build_domain_index(domain: str, model: SentenceTransformer) -> Dict:
    """
    Build complete index (BM25 + embeddings) for a single domain.
    
    Args:
        domain: Domain name
        model: SentenceTransformer model
        
    Returns:
        Dictionary with index components
    """
    print(f"\n[INDEX] Building index for domain: {domain}")
    
    # Load documents
    doc_tuples = load_documents_from_domain(domain)
    
    if not doc_tuples:
        print(f"[INDEX] No documents found for {domain}")
        return None
    
    documents = [doc[0] for doc in doc_tuples]
    filepaths = [doc[1] for doc in doc_tuples]
    
    print(f"[INDEX] Loaded {len(documents)} documents")
    
    # Build BM25 index
    print(f"[INDEX] Building BM25 index...")
    bm25 = build_bm25_index(documents)
    
    # Build embedding index
    print(f"[INDEX] Building embedding index...")
    embeddings = build_embedding_index(documents, model)
    
    # Create metadata
    metadata = {
        'documents': documents,
        'filepaths': filepaths,
        'domain': domain,
        'num_docs': len(documents)
    }
    
    index_data = {
        'bm25': bm25,
        'embeddings': embeddings,
        'metadata': metadata
    }
    
    return index_data


def build_global_index(model: SentenceTransformer) -> Dict:
    """
    Build global index combining all domains.
    
    Used when company="None" to search across all domains.
    
    Args:
        model: SentenceTransformer model
        
    Returns:
        Dictionary with global index components
    """
    print(f"\n[INDEX] Building global index (all domains)")
    
    all_documents = []
    all_filepaths = []
    all_domains = []
    
    # Collect documents from all domains
    for domain in DOMAINS:
        doc_tuples = load_documents_from_domain(domain)
        for doc, filepath in doc_tuples:
            all_documents.append(doc)
            all_filepaths.append(filepath)
            all_domains.append(domain)
    
    if not all_documents:
        print(f"[INDEX] No documents found for global index")
        return None
    
    print(f"[INDEX] Loaded {len(all_documents)} documents across all domains")
    
    # Build BM25 index
    print(f"[INDEX] Building global BM25 index...")
    bm25 = build_bm25_index(all_documents)
    
    # Build embedding index
    print(f"[INDEX] Building global embedding index...")
    embeddings = build_embedding_index(all_documents, model)
    
    # Create metadata
    metadata = {
        'documents': all_documents,
        'filepaths': all_filepaths,
        'domains': all_domains,
        'domain': 'global',
        'num_docs': len(all_documents)
    }
    
    index_data = {
        'bm25': bm25,
        'embeddings': embeddings,
        'metadata': metadata
    }
    
    return index_data


def build_all_indexes():
    """
    Build all indexes: per-domain and global.
    
    Main entry point for indexing process.
    """
    print("=" * 80)
    print("BUILDING HYBRID RAG INDEXES")
    print("=" * 80)
    
    # Load embedding model
    print(f"\n[INDEX] Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    # Build per-domain indexes
    for domain in DOMAINS:
        index_data = build_domain_index(domain, model)
        if index_data:
            save_index(index_data, domain)
    
    # Build global index
    global_index = build_global_index(model)
    if global_index:
        save_index(global_index, 'global')
    
    print("\n" + "=" * 80)
    print("INDEXING COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    build_all_indexes()
