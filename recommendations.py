# ==============================
# recommendation.py
# ==============================
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer, util

# ==============================
#  Connect to MongoDB and Load Data
# ==============================
def load_data_from_mongo(uri, db_name, collection_name):
    """
    Load project data from MongoDB and prepare it for embeddings.
    Ensure all necessary columns exist and combine idea + sector into one text field.
    """
    client = MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]

    data = pd.DataFrame(list(collection.find()))

    # Ensure required columns exist
    for col, default in {
        "idea": "",
        "sector": "",
        "capital_needed": 0,
        "capital_current": 0,
    }.items():
        if col not in data.columns:
            data[col] = default

    # Convert types
    data["idea"] = data["idea"].astype(str)
    data["sector"] = data["sector"].astype(str)
    data["capital_needed"] = pd.to_numeric(data["capital_needed"], errors="coerce").fillna(0)
    data["capital_current"] = pd.to_numeric(data["capital_current"], errors="coerce").fillna(0)

    # Combine idea and sector for embeddings
    data["text"] = data["idea"] + " sector: " + data["sector"]
    return data

# ==============================
#  Load Sentence-BERT Model
# ==============================
model = SentenceTransformer("all-MiniLM-L6-v2")

# ==============================
#  Recommend Projects for Investor
# ==============================
def recommend_projects_for_investor(all_projects, investor_interest):
    """
    Recommend all projects for an investor based on their interest.
    Sort projects by similarity descending.
    """
    df = pd.DataFrame(all_projects)

    if df.empty:
        return []

    # Ensure columns exist
    for col in ["title", "description", "goals", "sector"]:
        if col not in df.columns:
            df[col] = ""

    # Combine project text for embeddings safely
    df["text"] = (
        df["title"].fillna("") + " " +
        df["description"].fillna("") + " " +
        df["goals"].fillna("") + " " +
        df["sector"].fillna("")
    )

    # Encode investor interest
    investor_embedding = model.encode(investor_interest, convert_to_numpy=True)

    # Encode all projects
    project_embeddings = model.encode(df["text"].tolist(), convert_to_numpy=True)

    # Compute cosine similarity between investor and projects
    similarities = util.cos_sim(investor_embedding, project_embeddings)[0]
    df["similarity"] = similarities

    # Sort projects by similarity descending
    df_sorted = df.sort_values(by="similarity", ascending=False)

    return df_sorted.to_dict(orient="records")

# ==============================
#  Recommend Investors for Founder
# ==============================
def recommend_investors_for_founder_project(project_data, mongo_uri, db_name, threshold=0.2):
    from pymongo import MongoClient
    from sentence_transformers import SentenceTransformer, util
    from sklearn.metrics.pairwise import cosine_similarity

    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = MongoClient(mongo_uri)
    db = client[db_name]
    users = list(db.users.find({"role": {"$regex": "^investor$", "$options": "i"}}))

    if not users:
        return []

    project_text = f"{project_data.get('idea','')} {project_data.get('description','')} {project_data.get('sector','')}"
    proj_emb = model.encode([project_text], convert_to_numpy=True)

    results = []
    for u in users:
        poll = u.get("poll", {})
        investor_text = " ".join([str(v) for v in poll.values()])
        investor_sector = u.get("sector", "")
        full_text = investor_text + " " + investor_sector
        inv_emb = model.encode([full_text], convert_to_numpy=True)
        sim = cosine_similarity(proj_emb, inv_emb)[0][0]
        sector_bonus = 0.1 if project_data.get("sector", "").lower() == investor_sector.lower() else 0
        score = sim + sector_bonus
        if score >= threshold:
            results.append({
                "name": u.get("name", ""),
                "email": u.get("email", ""),
                "poll": poll,
                "sector": investor_sector,
                "similarity": float(score)
            })
    return sorted(results, key=lambda x: x["similarity"], reverse=True)
