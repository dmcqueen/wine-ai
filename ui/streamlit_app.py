import os, html, logging, requests, streamlit as st
from typing import List, Dict

st.set_page_config(page_title="Wine-AI Pairings", page_icon="🍷")

TIMEOUT = (3.5, 10)          # (connect, read) seconds
MAX_TEXT_LEN = 256           # enforce small queries
MAX_VECTOR_LEN = 384         # expected MiniLM dimensionality
MAX_K = 20                   # upper bound from UI

VESPA_ENDPOINT = st.secrets["vespa"]["endpoint"]       
EMBED_ENDPOINT = st.secrets["embed"]["endpoint"]       
VESPA_API_KEY  = st.secrets["vespa"]["api_key"]   # optional token auth

vespa_session = requests.Session()
vespa_session.headers.update({
    "User-Agent": "Wine-AI/1.0",
})

if VESPA_API_KEY:
    vespa_session.headers["Authorization"] = f"Bearer {VESPA_API_KEY}"

###############################################################################
# 2. Streamlit UI
###############################################################################
st.title("Wine-AI — Semantic Wine Pairings")

query = st.text_input("Describe your dish, mood or wine style", max_chars=MAX_TEXT_LEN)
top_k = st.slider("Number of suggestions", 1, MAX_K, 5, step=1)

rank_ui = st.radio(
    "Ranking mode",
    ("Vector", "Keyword (default)", "Keyword (default_2)"),
    horizontal=True,
)

def build_keyword_params(q: str, ranking: str, k: int) -> Dict[str, str]:
    return {
        "yql":  "select id,winery,variety,description "
                "from wine where userInput(@userquery) limit {k};",
        "ranking": ranking,
        "userquery": q,
        "k": str(k),
    }

def _safe_vector(q: str) -> List[float]:
    embed_session = requests.Session()
    embed_session.headers.update({
        "User-Agent": "Wine-AI/1.0",
    })
    resp = embed_session.post(f"{EMBED_ENDPOINT}",
                        json={"text": q},
                        timeout=TIMEOUT,
                        verify=True)
    resp.raise_for_status()
    vec = resp.json().get("paraphrase-multilingual-MiniLM-L12-v2")
    if not isinstance(vec, list) or len(vec) != MAX_VECTOR_LEN:
        raise ValueError("Embedding service returned invalid vector size")
    return vec

def build_vector_params(q: str, k: int) -> Dict:
    vec = _safe_vector(q)
    return {
        "yql":
            "select id,winery,variety,description from wine where "
            f"([{{\"targetHits\":{k}}}]nearestNeighbor(description_vector, query_vector)) "
            f"limit {k};",
        "ranking": "vector",
        "k": str(k),
        "input.query(query_vector)": vec,
    }

if query:
    try:
        with st.spinner("Finding the perfect glass…"):
            params = (
                build_vector_params(query, top_k)
                if rank_ui == "Vector"
                else build_keyword_params(
                    query,
                    "default" if rank_ui.endswith("(default)") else "default_2",
                    top_k,
                )
            )

            res = vespa_session.post(f"{VESPA_ENDPOINT}/search/",
                               json=params, timeout=TIMEOUT, verify=True)

            res.raise_for_status()
            # if res.status_code != 200:
            #     logging.error("Vespa %s: %s", res.status_code, res.text)
            #     st.error(f"Vespa {res.status_code}: {res.json().get('message', res.text)}")
            #     st.stop()            

            hits = res.json().get("root", {}).get("children", [])[:top_k]

        if not hits:
            st.info("No matches, sorry. Try a different query.")
        else:
            for h in hits:
                f = h["fields"]
                title  = html.escape(f.get("title")   or f.get("variety") or "Unknown variety")
                winery = html.escape(f.get("winery", ""))
                desc   = html.escape(f.get("description", ""))

                st.markdown(f"### {title}")
                if winery:
                    st.write(f"**Winery:** {winery}")
                if desc:
                    st.write(desc)
                st.divider()

    except Exception as exc:
        logging.exception("Search failure")  
        st.error("Unexpected error - please try again later")
