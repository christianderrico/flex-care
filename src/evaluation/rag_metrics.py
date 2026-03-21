"""
Evaluation metrics for Retrieval and RAG component.
"""

def hit_k(contexts: list[list[str]], actuals: list[str]) -> float:
    """
    Computes the Hit@K metric: the fraction of queries for which the expected
    answer is present in the retrieved context.

    Args:
        contexts: List of retrieved contexts, one per query.
                  Each context is a list of strings (the retrieved documents).
        actuals:  List of expected answers, one per query.

    Returns:
        A float in [0.0, 1.0] representing the proportion of queries
        for which the expected item was found in the retrieved context.

    Example:
        >>> contexts = [["doc1", "doc2"], ["doc3"], ["doc1", "doc4"]]
        >>> actuals  = ["doc2", "doc3", "doc5"]
        >>> hit_k(contexts, actuals)
        0.6666666666666666
    """
    return sum(
        actual in context
        for actual, context in zip(actuals, contexts)
    ) / len(actuals)
