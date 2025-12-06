# app/llm.py
from typing import Dict, Any, List

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.config import GROQ_API_KEY, LLM_MODEL

# Base LLM client
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=LLM_MODEL,
    temperature=0.4,
)


def explain_playlist(preferences: Dict[str, Any],
                     new_tracks: List[Dict[str, Any]],
                     kept_tracks: List[Dict[str, Any]],
                     removed_tracks: List[Dict[str, Any]]) -> str:
    """Ask the LLM to write a human explanation of the playlist."""
    prompt = ChatPromptTemplate.from_template(
        """
You are an expert music curator building playlists using MusicBrainz data.

User preferences:
{preferences}

New tracks added in this session:
{new_tracks}

Tracks kept from previous playlist versions:
{kept_tracks}

Tracks removed since last time:
{removed_tracks}

Write a friendly, concise explanation (4–6 sentences) that:
- connects recommendations to their favorite artists, genres, and mood
- mentions that some artists are similar to their favorites
- briefly highlights what changed since the last session.
"""
    )

    chain = prompt | llm
    result = chain.invoke(
        {
            "preferences": preferences,
            "new_tracks": new_tracks,
            "kept_tracks": kept_tracks,
            "removed_tracks": removed_tracks,
        }
    )
    return result.content


def suggest_similar_artists(preferences: Dict[str, Any]) -> List[str]:
    """
    Use the LLM to expand the artist set based on
    favorite artists, genres and mood.

    Returns a list of artist names (strings).
    """
    fav_artists = ", ".join(preferences.get("artists") or [])
    fav_genres = ", ".join(preferences.get("genres") or [])
    mood = preferences.get("mood") or ""

    prompt = ChatPromptTemplate.from_template(
        """
You are a music recommendation expert.

Given this user profile:
- Favorite artists: {fav_artists}
- Favorite genres: {fav_genres}
- Mood: {mood}

Suggest 10 modern artists that this user is likely to enjoy.
Return ONLY a comma-separated list of artist names.
Do NOT include any explanations or numbering.
"""
    )

    chain = prompt | llm
    result = chain.invoke(
        {
            "fav_artists": fav_artists,
            "fav_genres": fav_genres,
            "mood": mood,
        }
    )

    raw = result.content or ""
    names = [n.strip() for n in raw.split(",") if n.strip()]
    # Deduplicate and keep nice capitalization
    seen = set()
    unique: List[str] = []
    for n in names:
        key = n.lower()
        if key not in seen:
            seen.add(key)
            unique.append(n)
    return unique
