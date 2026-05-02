"""
Hybrid retrieval module combining BM25 and dense embeddings.

Implements Hybrid RAG with Reciprocal Rank Fusion (RRF) to combine
sparse (BM25) and dense (embedding) retrieval results.
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from config import (
    INDEX_DIR,
    EMBEDDINGS_DIR,
    EMBEDDING_MODEL,
    BM25_TOP_K,
    EMBEDDING_TOP_K,
    TOP_K_BEFORE_RERANK,
    RRF_K
)


class HybridRetriever:
    """
    Hybrid retriever combining BM25 sparse and dense embedding retrieval.
    """
    
    def __init__(self, domain: str):
        """
        Initialize retriever for a specific domain.
        
        Args:
            domain: Domain name (hackerrank, claude, visa, or global)
        """
        self.domain = domain
        self.bm25 = None
        self.embeddings = None
        self.metadata = None
        self.embedding_model = None
        
        self._load_index()
    
    def _load_index(self):
        """Load BM25 index, embeddings, and metadata from disk."""
        # Load BM25 index
        bm25_path = os.path.join(INDEX_DIR, f"{self.domain}_bm25.pkl")
        if not os.path.exists(bm25_path):
            raise FileNotFoundError(f"BM25 index not found: {bm25_path}")
        
        with open(bm25_path, 'rb') as f:
            self.bm25 = pickle.load(f)
        
        # Load embeddings
        embeddings_path = os.path.join(EMBEDDINGS_DIR, f"{self.domain}_embeddings.npy")
        if not os.path.exists(embeddings_path):
            raise FileNotFoundError(f"Embeddings not found: {embeddings_path}")
        
        self.embeddings = np.load(embeddings_path)
        
        # Load metadata
        metadata_path = os.path.join(INDEX_DIR, f"{self.domain}_metadata.pkl")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata not found: {metadata_path}")
        
        with open(metadata_path, 'rb') as f:
            self.metadata = pickle.load(f)
        
        # Load embedding model
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    
    def _bm25_search(self, query: str, top_k: int = BM25_TOP_K) -> List[Tuple[int, float]]:
        """
        Perform BM25 sparse retrieval.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (doc_index, score) tuples
        """
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = [(int(idx), float(scores[idx])) for idx in top_indices]
        
        return results
    
    def _embedding_search(self, query: str, top_k: int = EMBEDDING_TOP_K) -> List[Tuple[int, float]]:
        """
        Perform dense embedding retrieval.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (doc_index, score) tuples
        """
        # Encode query
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        
        # Compute cosine similarity
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = [(int(idx), float(similarities[idx])) for idx in top_indices]
        
        return results
    
    def _reciprocal_rank_fusion(
        self,
        bm25_results: List[Tuple[int, float]],
        embedding_results: List[Tuple[int, float]],
        k: int = RRF_K
    ) -> List[Tuple[int, float]]:
        """
        Combine BM25 and embedding results using Reciprocal Rank Fusion.
        
        RRF formula: score = Σ 1/(k + rank_i)
        
        Args:
            bm25_results: Results from BM25 search
            embedding_results: Results from embedding search
            k: RRF constant (default 60)
            
        Returns:
            Fused results sorted by RRF score
        """
        rrf_scores = {}
        
        # Add BM25 ranks
        for rank, (doc_idx, _) in enumerate(bm25_results, start=1):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0) + 1 / (k + rank)
        
        # Add embedding ranks
        for rank, (doc_idx, _) in enumerate(embedding_results, start=1):
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0) + 1 / (k + rank)
        
        # Sort by RRF score
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_results
    
    def retrieve(self, query: str, top_k: int = TOP_K_BEFORE_RERANK) -> List[Dict]:
        """
        Perform hybrid retrieval combining BM25 and embeddings.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of document dictionaries with text and metadata
        """
        # Perform BM25 search
        bm25_results = self._bm25_search(query, BM25_TOP_K)
        
        # Perform embedding search
        embedding_results = self._embedding_search(query, EMBEDDING_TOP_K)
        
        # Fuse results with RRF
        fused_results = self._reciprocal_rank_fusion(bm25_results, embedding_results)
        
        # Get top-k documents
        top_results = fused_results[:top_k]
        
        # Build result documents
        documents = []
        for doc_idx, rrf_score in top_results:
            doc_text = self.metadata['documents'][doc_idx]
            doc_filepath = self.metadata['filepaths'][doc_idx]
            
            doc_dict = {
                'text': doc_text,
                'filepath': doc_filepath,
                'index': doc_idx,
                'rrf_score': rrf_score,
                'domain': self.metadata.get('domains', [self.domain])[doc_idx] if 'domains' in self.metadata else self.domain
            }
            
            documents.append(doc_dict)
        
        return documents


def retrieve_pages(query: str, company: str = None, top_k: int = TOP_K_BEFORE_RERANK) -> List[Dict]:
    """
    Retrieve relevant pages using hybrid retrieval.
    
    Args:
        query: Search query (should be rewritten query from query_rewriter)
        company: Company name (hackerrank, claude, visa) or None for global search
        top_k: Number of pages to retrieve before reranking
        
    Returns:
        List of retrieved document dictionaries
    """
    # Determine which index to use
    domain = company if company else 'global'
    
    try:
        # Initialize retriever
        retriever = HybridRetriever(domain)
        
        # Retrieve documents
        documents = retriever.retrieve(query, top_k)
        
        return documents
    
    except FileNotFoundError as e:
        print(f"[RETRIEVER] Error: {str(e)}")
        print(f"[RETRIEVER] Make sure to run page_index.py first to build indexes")
        return []
    
    except Exception as e:
        print(f"[RETRIEVER] Error during retrieval: {str(e)}")
        return []
