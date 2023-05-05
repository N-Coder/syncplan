import os
from pathlib import Path

import pymongo.database
from pymongo import MongoClient

# Connect MongoDB
name = os.getenv('SP_COLLECTION', 'stats')
kwargs = {}
f = Path(__file__).parent / "mongo-password.txt"
if f.exists():
    kwargs["password"] = f.read_text().strip()
db = pymongo.MongoClient(
    os.getenv("SP_MONGO_URL"),
    serverSelectionTimeoutMS=2000, **kwargs
).get_database(os.getenv("SP_MONGO_DB"))
coll: pymongo.collection.Collection = db[name]
