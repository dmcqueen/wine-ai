"""
streamlit_app.py - Streamlit UI for Wine-AI
---------------------------------
Mirrors the logic of search_wine.sh (keyword + vector modes).
"""

import os
import requests
import streamlit as st

# ───────────────────────────────
# 1. Configuration
# ───────────────────────────────
VESPA_ENDPOINT = os.getenv("VESPA_ENDPOINT", "http://vespa:8080")   # same defaults as the shell script
EMBED_ENDPOINT = os.getenv("EMBED_ENDPOINT", "http://models:8088")   # (no trailing “/embed”)

# ───────────────────────────────
# 2. Streamlit UI
# ───────────────────────────────
st.set_page_config(page_title="Wine-AI Pairings", page_icon="🍷")
st.title("Wine-AI -Semantic Wine Pairings")

query   = st.text_input("Describe your dish, mood or wine style")
top_k   = st.slider("Number of suggestions", 1, 20, 5)
rank_ui = st.radio(
    "Ranking mode",
    ("Vector", "Keyword (default)", "Keyword (default_2)"),
    horizontal=True,
)

# ───────────────────────────────
# 3. Helper builders (mirror shell)
# ───────────────────────────────
def build_keyword_payload(q: str, ranking: str) -> dict:
    tokens = q.split()
    cond   = " or ".join(f'description contains "{w}"' for w in tokens)
    yql    = (
        f"select id,winery,variety,description "
        f"from wine where {cond} limit {top_k} offset 0;"
    )
    return {"yql": yql, "ranking": ranking}

def build_vector_payload(q: str) -> dict:
    # call exactly the same embed endpoint the script hits
    r = requests.post(EMBED_ENDPOINT, json={"text": q}, timeout=10)
    r.raise_for_status()
    vec = r.json()["paraphrase-multilingual-MiniLM-L12-v2"]  # list[float]

    yql = (
        "select id,winery,variety,description from wine where "
        f"([{{\"targetHits\":{top_k}}}]nearestNeighbor(description_vector, query_vector)) "
        f"limit {top_k} offset 0;"
    )
    return {
        "yql": yql,
        "input.query(query_vector)": vec,
        "ranking": "vector",
    }

# ───────────────────────────────
# 4. Execute search
# ───────────────────────────────
if query:
    try:
        with st.spinner("Finding the perfect glass …"):
            if rank_ui == "Vector":
                payload = build_vector_payload(query)
            else:
                ranking = "default" if rank_ui.endswith("(default)") else "default_2"
                payload = build_keyword_payload(query, ranking)

            res = requests.post(f"{VESPA_ENDPOINT}/search/", json=payload, timeout=10)
            res.raise_for_status()
            hits = res.json().get("root", {}).get("children", [])[:top_k]

        # ───────────────────────
        # 5. Render results
        # ───────────────────────
        if not hits:
            st.info("No matches, sorry. Try a different query.")
        else:
            for h in hits:
                f      = h["fields"]
                title  = f.get("title") or f.get("variety") or "Unknown variety"
                winery = f.get("winery", "")
                desc   = f.get("description", "")

                st.markdown(f"### {title}")
                if winery:
                    st.write(f"**Winery:** {winery}")
                if desc:
                    st.write(desc)
                st.divider()

    except Exception as exc:
        st.error(f"Oops - {exc}")
