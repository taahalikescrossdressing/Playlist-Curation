# app/agents/intake_agent.py
import os
import json
from typing import Dict, Any

from app.config import BASE_DATA_DIR


def intake_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    First node in the graph:
    - Ensures 'user_id' and 'preferences' exist
    - Persists preferences to data/users/<user_id>/preferences.json
    - Returns the (possibly updated) state
    """
    user_id = state.get("user_id")
    preferences = state.get("preferences")

    if user_id is None:
        # This should never happen if MusicDiscoveryGraph.run is correct
        raise ValueError("intake_agent: 'user_id' is missing from state")

    if preferences is None:
        # If no preferences were passed, at least store an empty dict
        preferences = {}
        state["preferences"] = preferences

    user_dir = os.path.join(BASE_DATA_DIR, "users", str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    pref_path = os.path.join(user_dir, "preferences.json")
    with open(pref_path, "w", encoding="utf-8") as f:
        json.dump(preferences, f, indent=2, ensure_ascii=False)

    return state
