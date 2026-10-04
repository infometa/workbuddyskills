"""Privacy-bounded local search over durable project evidence."""

from mibao_core.search.fts import (
    SearchDocument,
    SearchResult,
    SearchValidationError,
    search_documents,
    upsert_search_documents,
)

__all__ = [
    "SearchDocument",
    "SearchResult",
    "SearchValidationError",
    "search_documents",
    "upsert_search_documents",
]
