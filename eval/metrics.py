from typing import List, Any, Set

def calculate_hit_at_k(retrieved_ids: List[Any], relevant_ids: Set[Any], k: int) -> bool:
    """Check if at least one relevant item is in the top k retrieved items."""
    top_k = retrieved_ids[:k]
    for item in top_k:
        if item in relevant_ids:
            return True
    return False

def calculate_reciprocal_rank(retrieved_ids: List[Any], relevant_ids: Set[Any]) -> float:
    """Calculate the reciprocal rank of the first relevant item."""
    for i, item in enumerate(retrieved_ids):
        if item in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0

def calculate_recall_at_k(retrieved_ids: List[Any], relevant_ids: Set[Any], k: int) -> float:
    """Calculate the fraction of relevant items retrieved in top k."""
    if not relevant_ids:
        return 0.0
    
    top_k = set(retrieved_ids[:k])
    intersection = top_k.intersection(relevant_ids)
    return len(intersection) / len(relevant_ids)
