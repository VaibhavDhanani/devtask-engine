from app.core.db.database import get_db, get_db_transactional

DbSession = get_db
TransactionalDbSession = get_db_transactional

# Backwards-compatible alias used by older code paths.
get_database_session = get_db

__all__ = [
    "DbSession",
    "TransactionalDbSession",
    "get_db",
    "get_db_transactional",
    "get_database_session",
]
