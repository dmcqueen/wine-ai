# wine_ai_pairings.py
import html, logging
from typing import Dict, List

import requests
import streamlit as st

# ─────────── Page & logging ───────────
st.set_page_config("Wine-AI Pairings", "🍇", layout="centered")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# ─────────── Global CSS ───────────
st.markdown("""
<style>
/* Allow multi-line labels & values inside st.metric */
div[data-testid="stMetricLabel"],
div[data-testid="stMetricValue"]{
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}
/* Leaner slider tick label */
.stSlider > div[data-baseweb="slider"] span{font-size:0.8rem !important}
/* Subtle card shadow */
section.main > div + div .element-container:has(hr){
    box-shadow:0 1px 4px rgba(0,0,0,0.05);
    border-radius:8px;padding:0.6rem 1rem;
    background:var(--secondary-background-color)
}

@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@700&display=swap');
.stApp h1 {
    font-family: 'Caveat', cursive !important;
    font-size: 3.09rem !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────── Constants ───────────
TIMEOUT, MAX_TEXT_LEN, MAX_K = (3.5, 10), 256, 20
MAX_VECTOR_LEN = 384            # MiniLM
VESPA_ENDPOINT  = st.secrets["vespa"]["endpoint"]
EMBED_ENDPOINT  = st.secrets["embed"]["endpoint"]
VESPA_API_KEY   = st.secrets["vespa"].get("api_key", "")

# ─────────── Sessions ───────────
vespa = requests.Session()
vespa.headers.update({
    "User-Agent": "Wine-AI/1.0",
    **({"Authorization": f"Bearer {VESPA_API_KEY}"} if VESPA_API_KEY else {})
})
embed = requests.Session()
embed.headers.update({"User-Agent": "Wine-AI/1.0"})

# ─────────── Helpers ───────────
@st.cache_data(show_spinner=False, ttl=3600)
def _get_embedding(text: str) -> List[float]:
    res = embed.post(EMBED_ENDPOINT, json={"text": text}, timeout=TIMEOUT)
    # res.raise_for_status()
    if res.status_code != 200:
        logging.error("Vespa %s: %s", res.status_code, res.text)
        st.error(f"Vespa {res.status_code}: {res.json().get('message', res.text)}")
        st.stop()         
    vec = res.json()["paraphrase-multilingual-MiniLM-L12-v2"]
    if len(vec) != MAX_VECTOR_LEN:
        raise ValueError("Bad vector length")
    return vec

def build_vector_params(q: str, ranking: str, k: int) -> Dict:
    return {
        "yql": (
            "select id, winery, variety, region_1, country, price, points, "
            "description from wine where "
            "([{ \"targetHits\": %d }]nearestNeighbor(description_vector, query_vector)) "
            "limit %d;" % (k, k)
        ),
        "ranking": ranking,
        "k": str(k),
        "input.query(query_vector)": _get_embedding(q),
    }

def build_keyword_params(q: str, ranking: str, k: int) -> Dict:
    """
    Build a pure keyword (BM-25 / NativeRank) query that searches the
    `description` field for every individual term in `q`, combined with OR.
    """
    words = [w.strip() for w in q.split() if w.strip()]
    if not words:
        words = [q.strip()]                     # fallback: whole string

    cond = " or ".join(f'description contains "{html.escape(w)}"' for w in words)

    yql = (
        "select id, winery, variety, region_1, country, price, points, "
        f'description from wine where {cond} limit {k};'
    )
    return {
        "yql"    : yql,
        "ranking": ranking,   # "default" or "default_2"
        "k"      : str(k)     # keep your custom rank‑profile feature
    }

def price_fmt(p):  # ‘Unknown’ on 0/None, 2‑decimals otherwise
    return "Unknown" if not p else f"${p:,.2f}" if isinstance(p, (int, float)) else str(p)

def hit_card(hit):
    f = hit["fields"]
    title    = f.get("variety") or "Unknown variety"
    winery   = f.get("winery", "") or "—"
    region   = f.get("region_1", "")
    country  = f.get("country", "")
    region_str = " · ".join(filter(None, [region, country])) or "—"
    price    = price_fmt(f.get("price"))
    points   = f.get("points", "—")
    desc     = f.get("description", "")

    # ── points badge (unchanged) ────────────────────────────────────────────────
    if isinstance(points, int):
        badge_colour = (
            "#136B13" if points >= 92
            else "#B28C00" if points >= 88
            else "#777"
        )
        badge_html = (
            f"<span style='background:{badge_colour};color:#fff;padding:2px 8px;"
            "border-radius:4px;font-size:0.82rem;white-space:nowrap'>"
            f"{points}&nbsp;pts"
            "</span>"
        )
    else:
        badge_html = ""

    # ── header row: title · winery (+ badge) ───────────────────────────────────
    header_html = (
        "<div style='display:flex;justify-content:space-between;"
        "align-items:center;margin-bottom:0.15rem'>"
        f"<h4 style='margin:0'>{html.escape(title)}&nbsp;·&nbsp;"
        f"{html.escape(winery)}</h4>"
        f"{badge_html}"
        "</div>"
    )

    # ── new single‑line italics for region / country / price ───────────────────
    subline_html = (
        f"<p style='font-style:italic;margin:-8px 0 15px 0;'>"
        f"{html.escape(region_str)} — {price}"
        "</p>"
    )

    with st.container():
        st.markdown(header_html, unsafe_allow_html=True)
        st.markdown(subline_html, unsafe_allow_html=True)   # ← new line

        if desc:
            st.write(desc)

        st.markdown("---")

# ─────────── UI  ───────────
st.title("🍇  Wine-Ai — Semantic Pairings")

q = st.text_input(
    "Describe your dish, mood, or wine style",
    placeholder="goes with seafood",
    max_chars=MAX_TEXT_LEN
)

top_k = st.slider(
    "Suggestions",                       # visible label
    1, MAX_K, 5,
    label_visibility="collapsed"         # keep label hidden if you like
)

# ── Ranking modes ───────────────────────────────────────────────────────────
RANKINGS = [
    (
        "Vector",
        "vector",
        "Query creates a 384-dimensional vector from a tensor server using SentenceTransformers. Vespa's closeness ranking compares that vector to the stored description embedding in each document with a nearestNeighbor query that uses an angular distance-metric on a HSNW index. It gives the smallest distance (largest similarity) a high score. Documents whose vector meaning sits closest to the query vector bubble to the top, regardless of exact keywords.",
    ),
    (
        "Vector, Points",
        "vector_2",
        "First phase, same vector closeness as Vector to pull back the most semantically similar results. Second phase, Vespa re-ranks just the top results by the numeric points attribute, so among equally close documents the ones with more “points” (quality score) rise higher.",
    ),
    (
        "BM25", 
        "default", 
        "Scores every document by the classic Okapi BM25 formula on the description field: it rewards documents that contain many occurrences of the query words, prefers rarer words (high IDF) and slightly normalises for field length. The higher this statistical match, the higher the rank."
    ),
    (
        "Vespa NativeRank", 
        "default_2", 
        "Vespa's built-in heuristic scorer. It mixes three signals—how well each field matches (nativeFieldMatch), how close the query words appear together (nativeProximity) and how well attribute fields match (nativeAttributeMatch)—into one number. It's BM25 enriched with proximity and attribute logic but still fast enough for first-phase ranking."
    ),
]

ranking_idx = st.radio(
    "Ranking mode",
    options=list(range(len(RANKINGS))),
    format_func=lambda i: RANKINGS[i][0],
    horizontal=True,
)
ranking_label, ranking_profile, ranking_expr = RANKINGS[ranking_idx]
st.markdown(
    f"<div style='border:1.5px solid #ddd; border-radius:8px; padding:0.8em 1em; background:#fafbfc; margin:1em 0;'>"
    f"{ranking_expr}"
    "</div>",
    unsafe_allow_html=True
)

if q:
    try:
        with st.spinner("Finding the perfect glass…"):
            params = (
                build_vector_params(q, ranking_profile, top_k)
                if ranking_label.startswith("Vector")
                else build_keyword_params(q, ranking_profile, top_k)
            )
            r = vespa.post(f"{VESPA_ENDPOINT}/search/", json=params, timeout=TIMEOUT)
            if r.status_code != 200:
                st.error(f"Vespa {r.status_code}: {r.json().get('message', 'Unknown error')}")
            else:
                hits = r.json().get("root", {}).get("children", [])[:top_k]
                if not hits:
                    st.info("No matches found — try phrasing it another way.")
                for h in hits:
                    hit_card(h)
    except Exception:
        logging.exception("Search failure")
        st.error("Something went wrong — please try again later")
