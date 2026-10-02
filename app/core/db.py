from pymongo import MongoClient, ASCENDING
from core.config import settings


client = MongoClient(settings.DATABASE_URL)
db = client.get_database()


# Collections
users_collection = db["users"]
documents_collection = db["documents"]
contracts_collection = db["contract"]
analysis_collection = db["analysis"]    



def init_db():
    # Create indexed for the collection if they don't exist
    
    users_collection.create_index("email", unique=True)
    users_collection.create_index("google_id", sparse=True)
   
    # documents: one file per user, unique filename per user
    documents_collection.create_index(
        [("user_id", ASCENDING), ("filename", ASCENDING)],
        unique=True
    )
    documents_collection.create_index("user_id")
    documents_collection.create_index("created_at")

    # analysis: keep history of queries per document
    analysis_collection.create_index(
        [("user_id", ASCENDING), ("document_id", ASCENDING)]
    )
    analysis_collection.create_index("document_id")
