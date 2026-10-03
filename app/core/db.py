from pymongo import MongoClient, ASCENDING, DESCENDING
from core.config import settings


client = MongoClient(settings.DATABASE_URL)
db = client.get_database()


# Collections
users_collection = db["users"]
documents_collection = db["documents"]
page_collection=db["page"]
contracts_collection = db["contract"]
analysis_collection = db["analysis"]    


# Chat 
chat_sessions_collection = db["chat_sessions"]
chat_messages_collection = db["chat_messages"]



def init_db() -> None:
    """Create indexes. Safe to call on every startup — Mongo is idempotent."""

    # --- users ---
    users_collection.create_index("email", unique=True)
    users_collection.create_index("google_id", sparse=True)

    # --- documents ---
    # one file per user, unique filename per user
    documents_collection.create_index(
        [("user_id", ASCENDING), ("filename", ASCENDING)],
        unique=True,
    )
    # list a user's documents newest-first
    documents_collection.create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)]
    )
    # look up by slug (for /documents/{doc_slug})
    documents_collection.create_index("slug", unique=True, sparse=True)

    # --- pages ---
    page_collection.create_index(
        [("doc_id", ASCENDING), ("page_number", ASCENDING)],
        unique=True,
    )

    # --- analysis ---
    analysis_collection.create_index(
        [("user_id", ASCENDING), ("document_id", ASCENDING)]
    )
    analysis_collection.create_index("document_id")

    # --- chat ---
    chat_sessions_collection.create_index(
        [("user_id", ASCENDING), ("updated_at", DESCENDING)]
    )
    chat_sessions_collection.create_index("document_id")

    chat_messages_collection.create_index(
        [("session_id", ASCENDING), ("created_at", ASCENDING)]
    )