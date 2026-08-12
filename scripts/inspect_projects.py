import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db
from search_utils import build_project_search_query, expand_search_terms, backfill_project_sectors

backfill_project_sectors(db)

projects = list(db.projects.find({}, {
    'title': 1, 'description': 1, 'sector': 1, 'tags': 1,
}).limit(20))

with open('scripts/projects_sample.json', 'w', encoding='utf-8') as f:
    json.dump([{**p, '_id': str(p['_id'])} for p in projects], f, ensure_ascii=False, indent=2)

with open('scripts/search_debug.txt', 'w', encoding='utf-8') as f:
    for q in ['technology', 'زراعه', 'صناعه', 'agriculture', 'tech', 'farm']:
        query = build_project_search_query(q)
        count = db.projects.count_documents(query)
        matches = list(db.projects.find(query, {'title': 1, 'sector': 1}).limit(5))
        f.write(f'\n=== {q} ===\ncount: {count}\n')
        for m in matches:
            f.write(f"  - {m.get('title')} [{m.get('sector')}]\n")

print('done', len(projects))
