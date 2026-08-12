"""
Migrate local MongoDB (Compass) data to MongoDB Atlas.

Usage (PowerShell):
  $env:ATLAS_URI="mongodb+srv://USER:PASS@cluster0.xxxxx.mongodb.net/graduation?retryWrites=true&w=majority"
  python scripts/migrate_to_atlas.py

Optional:
  $env:LOCAL_URI="mongodb://localhost:27017"
  $env:MONGO_DB="graduation"
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pymongo import MongoClient
from pymongo.errors import BulkWriteError

LOCAL_URI = os.getenv('LOCAL_URI', 'mongodb://localhost:27017')
ATLAS_URI = os.getenv('ATLAS_URI', '').strip()
DB_NAME = os.getenv('MONGO_DB', 'graduation')

SKIP_COLLECTIONS = {'system.indexes', 'system.profile'}


def copy_collection(local_db, atlas_db, name):
    src = local_db[name]
    dst = atlas_db[name]
    docs = list(src.find({}))
    if not docs:
        print(f'  {name}: empty — skipped')
        return 0
    dst.delete_many({})
    try:
        result = dst.insert_many(docs, ordered=False)
        count = len(result.inserted_ids)
    except BulkWriteError as e:
        count = e.details.get('nInserted', 0)
    print(f'  {name}: {count} documents')
    return count


def main():
    if not ATLAS_URI:
        print('ERROR: Set ATLAS_URI environment variable to your Atlas connection string.')
        print('Example:')
        print('  mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/graduation?retryWrites=true&w=majority')
        sys.exit(1)

    print(f'Local:  {LOCAL_URI} / {DB_NAME}')
    print(f'Atlas:  {ATLAS_URI.split("@")[-1] if "@" in ATLAS_URI else ATLAS_URI}')
    print()

    local_client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=8000)
    local_client.admin.command('ping')
    local_db = local_client[DB_NAME]

    atlas_client = MongoClient(ATLAS_URI, serverSelectionTimeoutMS=15000)
    atlas_client.admin.command('ping')
    atlas_db = atlas_client[DB_NAME]

    collections = [c for c in local_db.list_collection_names() if c not in SKIP_COLLECTIONS]
    print(f'Collections to migrate: {len(collections)}')
    print('-' * 40)

    total = 0
    for name in sorted(collections):
        total += copy_collection(local_db, atlas_db, name)

    print('-' * 40)
    print(f'Done. Total documents copied: {total}')
    print()
    print('Verify in Atlas Compass or mongosh, then set MONGO_URI on Render to ATLAS_URI.')


if __name__ == '__main__':
    main()
