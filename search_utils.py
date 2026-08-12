"""Bilingual (Arabic/English) search helpers for MongoDB queries."""
import re
import unicodedata

SEARCH_FIELDS = ('title', 'description', 'founder_name', 'goals', 'status', 'sector', 'contact_email', 'tags')

ARABIC_DIACRITICS = re.compile(r'[\u064B-\u065F\u0670\u0640]')
ARABIC_CHARS = re.compile(r'[\u0600-\u06FF]')

# Sector -> keywords found in project title/description/goals (EN + AR roots/words)
SECTOR_KEYWORDS = {
    'technology': [
        'technology', 'tech', 'software', 'app', 'platform', 'ai', 'artificial',
        'digital', 'smart', 'mobile', 'saas', 'freelanc', 'nft', 'ecommerce', 'e-commerce',
        'online', 'web', 'automation', 'robot', 'data', 'cloud', 'cyber', 'inventory',
        'pos', 'digitiz', 'marketplace', 'hub', 'teletherapy', 'chatbot',
        'تكنولوج', 'تقن', 'تطبيق', 'ذكاء', 'اصطناع', 'رقم', 'منصه', 'منصة', 'برمج',
    ],
    'agriculture': [
        'agriculture', 'agri', 'farm', 'farmer', 'crop', 'harvest', 'livestock',
        'greenhouse', 'food', 'organic', 'table', 'produce',
        'زراع', 'مزر', 'محصول', 'فلاح', 'حاص', 'زراعه', 'مزرعه', 'مزرعة', 'المزرعه',
    ],
    'industry': [
        'industry', 'industrial', 'manufactur', 'factory', 'production', 'supply',
        'packaging', 'recycling', 'waste', 'material',
        'صناع', 'مصنع', 'انتاج', 'إنتاج', 'تصنيع', 'صناعه', 'صناعة', 'صناعي',
    ],
    'healthcare': [
        'health', 'medical', 'therapy', 'mental', 'hospital', 'clinic', 'wellness',
        'counseling', 'teletherapy', 'support',
        'صح', 'طب', 'علاج', 'نفس', 'طبي', 'صحي', 'صحة',
    ],
    'education': [
        'education', 'edtech', 'learning', 'school', 'student', 'course', 'training',
        'تعليم', 'تعلم', 'مدرس', 'طلاب', 'دورات',
    ],
    'finance': [
        'finance', 'fintech', 'bank', 'payment', 'invest', 'capital', 'fund', 'escrow',
        'مال', 'تمويل', 'بنك', 'دفع', 'استثمار',
    ],
    'commerce': [
        'commerce', 'retail', 'store', 'shop', 'merchant', 'ecommerce', 'marketplace', 'art',
        'تجاره', 'تجارة', 'متجر', 'بيع', 'تسوق',
    ],
}

# User query (normalized) -> sector keys
QUERY_SECTOR_ALIASES = {
    'technology': ['technology'], 'tech': ['technology'], 'تكنولوجيا': ['technology'],
    'التكنولوجيا': ['technology'], 'تقنية': ['technology'], 'تقنيه': ['technology'],
    'agriculture': ['agriculture'], 'agri': ['agriculture'], 'farm': ['agriculture'],
    'زراعة': ['agriculture'], 'زراعه': ['agriculture'], 'الزراعة': ['agriculture'], 'زراعي': ['agriculture'],
    'industry': ['industry'], 'manufacturing': ['industry'], 'factory': ['industry'],
    'صناعة': ['industry'], 'صناعه': ['industry'], 'صناعي': ['industry'], 'مصنع': ['industry'],
    'health': ['healthcare'], 'healthcare': ['healthcare'], 'medical': ['healthcare'],
    'صحة': ['healthcare'], 'طب': ['healthcare'], 'طبي': ['healthcare'],
    'education': ['education'], 'تعليم': ['education'],
    'finance': ['finance'], 'fintech': ['finance'], 'تمويل': ['finance'], 'مالية': ['finance'],
    'retail': ['commerce'], 'commerce': ['commerce'], 'تجارة': ['commerce'], 'تجاره': ['commerce'],
    'open': ['status'], 'closed': ['status'], 'مفتوح': ['status'], 'مغلق': ['status'],
}

BILINGUAL_GROUPS = [
    ['open', 'مفتوح', 'مفتوحة'],
    ['closed', 'مغلق', 'مغلقة'],
    ['in progress', 'progress', 'قيد التنفيذ'],
]


def has_arabic(text: str) -> bool:
    return bool(ARABIC_CHARS.search(text or ''))


def normalize_ar(text: str) -> str:
    if not text:
        return ''
    text = ARABIC_DIACRITICS.sub('', text)
    text = unicodedata.normalize('NFKC', text)
    for src, dst in {'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ى': 'ي', 'ئ': 'ي', 'ة': 'ه', 'ؤ': 'و'}.items():
        text = text.replace(src, dst)
    return text.strip().lower()


def normalize_term(text: str) -> str:
    text = (text or '').strip().lower()
    if has_arabic(text):
        return normalize_ar(text)
    return text


def escape_regex(text: str) -> str:
    return re.escape(text)


def _sectors_for_query(query: str) -> set[str]:
    sectors = set()
    full = normalize_term(query)
    if full in QUERY_SECTOR_ALIASES:
        sectors.update(QUERY_SECTOR_ALIASES[full])

    for token in re.split(r'\s+', query):
        norm = normalize_term(token.strip())
        if norm in QUERY_SECTOR_ALIASES:
            sectors.update(QUERY_SECTOR_ALIASES[norm])

    for group in BILINGUAL_GROUPS:
        norms = {normalize_term(g) for g in group}
        if full in norms:
            continue
        for token in re.split(r'\s+', query):
            if normalize_term(token) in norms:
                break
    return {s for s in sectors if s != 'status'}


def expand_search_terms(query: str) -> list[str]:
    query = (query or '').strip()
    if not query:
        return []

    terms = {query, normalize_term(query)}
    for token in re.split(r'\s+', query):
        token = token.strip()
        if len(token) >= 2:
            terms.add(token)
            terms.add(normalize_term(token))

    for group in BILINGUAL_GROUPS:
        norms = {normalize_term(g) for g in group}
        if normalize_term(query) in norms:
            terms.update(group)
            break

    cleaned, seen = [], set()
    for t in terms:
        t = t.strip()
        if t and t not in seen:
            seen.add(t)
            cleaned.append(t)
    return cleaned[:20]


def _collect_patterns(query: str, terms: list[str]) -> list[str]:
    patterns = set()

    for term in terms:
        if len(term) < 2:
            continue
        if has_arabic(term):
            # Arabic: use normalized substring roots (3+ chars) for flexible matching
            norm = normalize_ar(term)
            if len(norm) >= 3:
                patterns.add(norm[: max(3, len(norm))])
            if len(norm) >= 4:
                patterns.add(norm[:4])
            patterns.add(norm)
        else:
            patterns.add(escape_regex(term))

    for sector in _sectors_for_query(query):
        for kw in SECTOR_KEYWORDS.get(sector, []):
            if len(kw) < 3:
                continue
            if has_arabic(kw):
                patterns.add(normalize_ar(kw))
            else:
                patterns.add(escape_regex(kw))

    # Dedupe, prefer longer patterns, cap count
    result = sorted(patterns, key=len, reverse=True)[:35]
    return [p for p in result if p]


def infer_sector(title='', description='', goals='') -> str:
    """Guess sector from project text for tagging/backfill."""
    raw = f'{title} {description} {goals}'
    text = raw.lower()
    text_ar = normalize_ar(raw)
    scores = {}
    for sector, keywords in SECTOR_KEYWORDS.items():
        score = 0
        for kw in keywords:
            kw_low = kw.lower()
            kw_ar = normalize_ar(kw)
            if kw_low in text or (kw_ar and kw_ar in text_ar):
                score += 2 if len(kw) >= 5 else 1
        if score:
            scores[sector] = score
    if not scores:
        return 'general'
    return max(scores, key=scores.get)


def infer_tags(title='', description='', goals='', sector='') -> list[str]:
    tags = set()
    if sector and sector != 'general':
        tags.add(sector)
    for sector_key, keywords in SECTOR_KEYWORDS.items():
        text = f'{title} {description} {goals}'.lower()
        text_ar = normalize_ar(f'{title} {description} {goals}')
        for kw in keywords[:8]:
            if kw.lower() in text or normalize_ar(kw) in text_ar:
                tags.add(sector_key)
                break
    return list(tags)


def backfill_project_sectors(db):
    """Set sector/tags on projects missing them."""
    cursor = db['projects'].find({
        '$or': [
            {'sector': {'$exists': False}},
            {'sector': None},
            {'sector': ''},
            {'sector': 'general'},
        ]
    })
    for p in cursor:
        sector = infer_sector(p.get('title', ''), p.get('description', ''), p.get('goals', ''))
        tags = infer_tags(p.get('title', ''), p.get('description', ''), p.get('goals', ''), sector)
        db['projects'].update_one({'_id': p['_id']}, {'$set': {'sector': sector, 'tags': tags}})


def build_project_search_query(search_q: str, lang: str = None) -> dict:
    terms = expand_search_terms(search_q)
    patterns = _collect_patterns(search_q, terms)
    if not patterns:
        return {}

    regex = '|'.join(patterns)
    or_conditions = [{field: {'$regex': regex, '$options': 'i'}} for field in SEARCH_FIELDS]
    # Also match tags array
    or_conditions.append({'tags': {'$in': list(_sectors_for_query(search_q))}})
    return {'$or': or_conditions}
