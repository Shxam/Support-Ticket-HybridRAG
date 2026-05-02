"""
Cross-encoder reranking module for Advanced RAG.

Post-retrieval reranking using cross-encoder to select the most relevant
documents from the hybrid retrieval candidates.
"""

from typing import List, Dict
from sentence_transformers import CrossEncoder
from config import RERANKER_MODEL, TOP_K_RETRIEVAL


class Reranker:
    """
    Cross-encoder reranker for post-retrieval refinement.
    """
    
    def __init__(self):
        """Initialize cross-encoder model."""
        self.model = CrossEncoder(RERANKER_MODEL)
    
    def rerank(self, query: str, documents: List[Dict], top_k: int = TOP_K_RETRIEVAL) -> List[Dict]:
        """
        Rerank documents using cross-encoder.
        
        Args:
            query: Search query
            documents: List of document dictionaries from retrieval
            top_k: Number of top documents to return
            
        Returns:
            Reranked list of top-k documents
        """
        if not documents:
            return []
        
        # Prepare query-document pairs
        pairs = [(query, doc['text']) for doc in documents]
        
        # Get cross-encoder scores
        scores = self.model.predict(pairs)
        
        # Add scores to documents
        for doc, score in zip(documents, scores):
            doc['rerank_score'] = float(score)
        
        # Sort by rerank score
        reranked_docs = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)
        
        # Return top-k
        return reranked_docs[:top_k]


# Global reranker instance (loaded once)
_reranker_instance = None


def get_reranker() -> Reranker:
    """
    Get or create global reranker instance.
    
    Returns:
        Reranker instance
    """
    global _reranker_instance
    
    if _reranker_instance is None:
        _reranker_instance = Reranker()
    
    return _reranker_instance


def rerank_documents(query: str, documents: List[Dict], top_k: int = TOP_K_RETRIEVAL) -> List[Dict]:
    """
    Rerank documents using cross-encoder.
    
    Main entry point for reranking.
    
    Args:
        query: Search query
        documents: List of document dictionaries from hybrid retrieval
        top_k: Number of top documents to return after reranking
        
    Returns:
        Reranked list of top-k documents
    """
    reranker = get_reranker()
    return reranker.rerank(query, documents, top_k)
