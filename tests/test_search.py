"""Tests for bilingual search utilities."""
from search_utils import (
    expand_search_terms,
    normalize_ar,
    build_project_search_query,
    infer_sector,
    backfill_project_sectors,
)


def test_normalize_ar():
    assert normalize_ar('مُؤَسِّس') == 'موسس'
    assert normalize_ar('إستثمار') == 'استثمار'
    assert normalize_ar('زراعه') == 'زراعه'
    assert normalize_ar('زراعة') == 'زراعه'


def test_expand_arabic_agriculture():
    terms = expand_search_terms('زراعه')
    assert 'زراعه' in terms


def test_infer_sector_farm():
    assert infer_sector('Farm to Table', 'connecting farmers', '') == 'agriculture'


def test_infer_sector_tech():
    assert infer_sector('Freelancer Hub', 'AI-powered platform', '') == 'technology'


def test_infer_sector_arabic_farm():
    assert infer_sector('المزرعه السعيده', 'حمايه المحاصيل', '') == 'agriculture'


def test_build_query_technology_finds_ai_projects():
    q = build_project_search_query('technology')
    assert '$or' in q
    regex = q['$or'][0]['title']['$regex']
    assert 'ai' in regex.lower() or 'tech' in regex.lower()


def test_build_query_agriculture_finds_farm():
    q = build_project_search_query('زراعه')
    assert '$or' in q


def test_backfill_sets_sector():
    class FakeCol:
        def __init__(self):
            self.docs = [{
                '_id': 1,
                'title': 'Farm to Table',
                'description': 'farmers market',
                'goals': '',
                'sector': None,
            }]
            self.updates = []

        def find(self, _):
            return self.docs

        def update_one(self, filt, upd):
            self.updates.append(upd)
            self.docs[0].update(upd['$set'])

    db = {'projects': FakeCol()}
    backfill_project_sectors(db)
    assert db['projects'].docs[0]['sector'] == 'agriculture'
    assert 'agriculture' in db['projects'].docs[0]['tags']


def test_empty_query():
    assert build_project_search_query('') == {}
    assert expand_search_terms('') == []
