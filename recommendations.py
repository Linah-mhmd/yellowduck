# ==============================
# recommendations.py — lightweight TF-IDF matching (no torch)
# ==============================
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _text_similarity(query: str, texts: list) -> list:
    """Return cosine similarity between query and each text."""
    cleaned = [str(t or '').strip() for t in texts]
    if not cleaned or not str(query or '').strip():
        return [0.0] * len(cleaned)
    corpus = [str(query).strip()] + cleaned
    vectorizer = TfidfVectorizer(stop_words='english', max_features=3000)
    matrix = vectorizer.fit_transform(corpus)
    return cosine_similarity(matrix[0:1], matrix[1:])[0].tolist()


def recommend_projects_for_investor(all_projects, investor_interest):
    """Recommend projects for an investor based on interest text."""
    df = pd.DataFrame(all_projects)
    if df.empty:
        return []

    for col in ['title', 'description', 'goals', 'sector']:
        if col not in df.columns:
            df[col] = ''

    df['text'] = (
        df['title'].fillna('') + ' '
        + df['description'].fillna('') + ' '
        + df['goals'].fillna('') + ' '
        + df['sector'].fillna('')
    )

    df['similarity'] = _text_similarity(investor_interest, df['text'].tolist())
    return df.sort_values(by='similarity', ascending=False).to_dict(orient='records')


def recommend_investors_for_founder_project(project_data, mongo_uri, db_name, threshold=0.2):
    """Recommend investors for a founder project."""
    from pymongo import MongoClient

    client = MongoClient(mongo_uri)
    db = client[db_name]
    users = list(db.users.find({'role': {'$regex': '^investor$', '$options': 'i'}}))
    if not users:
        return []

    project_text = ' '.join([
        str(project_data.get('idea', '')),
        str(project_data.get('description', '')),
        str(project_data.get('sector', '')),
    ]).strip()
    project_sector = str(project_data.get('sector', '')).lower()

    investor_texts = []
    for u in users:
        poll = u.get('poll', {})
        investor_text = ' '.join(str(v) for v in poll.values())
        investor_sector = u.get('sector', '')
        investor_texts.append(f'{investor_text} {investor_sector}'.strip())

    scores = _text_similarity(project_text, investor_texts)
    results = []
    for u, sim in zip(users, scores):
        investor_sector = u.get('sector', '')
        sector_bonus = 0.1 if project_sector and project_sector == str(investor_sector).lower() else 0
        score = float(sim) + sector_bonus
        if score >= threshold:
            results.append({
                'name': u.get('name', ''),
                'email': u.get('email', ''),
                'poll': u.get('poll', {}),
                'sector': investor_sector,
                'similarity': score,
            })
    return sorted(results, key=lambda x: x['similarity'], reverse=True)
