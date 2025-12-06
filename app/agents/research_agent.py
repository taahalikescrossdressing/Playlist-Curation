# app/agents/research_agent.py
import os
import json
from typing import Dict, Any, List

import requests

from app.config import BASE_DATA_DIR, MUSICBRAINZ_USER_AGENT
from app.llm import suggest_similar_artists

HEADERS = {"User-Agent": MUSICBRAINZ_USER_AGENT}
MB_BASE = "https://musicbrainz.org/ws/2"


def mb_artist_search(name: str) -> Dict[str, Any]:
    resp = requests.get(
        f"{MB_BASE}/artist/",
        params={"query": name, "fmt": "json", "limit": 1},
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def mb_recordings_by_artist(mbid: str, limit: int = 20) -> Dict[str, Any]:
    resp = requests.get(
        f"{MB_BASE}/recording",
        params={"artist": mbid, "limit": limit, "fmt": "json"},
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def _fetch_artist_block(name: str, max_rec: int) -> Dict[str, Any]:
    """
    Given an artist name, look them up on MusicBrainz and pull some recordings.
    Returns a dict with keys: name, mbid, recordings.
    """
    data = mb_artist_search(name)
    items = data.get("artists", [])
    if not items:
        return {"name": name, "error": "not_found"}

    info = items[0]
    mbid = info["id"]

    try:
        recs = mb_recordings_by_artist(mbid, limit=max_rec)
    except Exception as e:
        recs = {"error": str(e)}

    return {
        "name": info.get("name", name),
        "mbid": mbid,
        "artist_info": info,
        "recordings": recs,
    }


def research_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build research state:
      - seed_artists: user favorites with MusicBrainz recordings
      - similar_artists: LLM-suggested similar artists with recordings
    """
    user_id = state["user_id"]
    prefs = state["preferences"]

    seed_names: List[str] = [a.strip() for a in prefs.get("artists", []) if a.strip()]
    research: Dict[str, Any] = {
        "seed_artists": {},
        "similar_artists": {},
    }

    # ---- Seed artists ----
    for name in seed_names:
        try:
            block = _fetch_artist_block(name, max_rec=30)
            research["seed_artists"][name] = block
        except Exception as e:
            research["seed_artists"][name] = {"name": name, "error": str(e)}

    # ---- LLM-based similar artists ----
    try:
        llm_suggestions = suggest_similar_artists(prefs)
    except Exception as e:
        llm_suggestions = []
        research["similar_artists_error"] = str(e)

    # remove exact duplicates of favorites (case-insensitive)
    seed_lower = {s.lower() for s in seed_names}
    filtered_similar = [n for n in llm_suggestions if n.lower() not in seed_lower]

    for name in filtered_similar:
        try:
            block = _fetch_artist_block(name, max_rec=15)
            # we store by name so playlist_agent can loop over values
            research["similar_artists"][name] = block
        except Exception as e:
            research["similar_artists"][name] = {"name": name, "error": str(e)}

    # ---- Persist to filesystem ----
    user_dir = os.path.join(BASE_DATA_DIR, "users", str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    with open(os.path.join(user_dir, "research.json"), "w", encoding="utf-8") as f:
        json.dump(research, f, indent=2, ensure_ascii=False)

    state["research"] = research
    return state
