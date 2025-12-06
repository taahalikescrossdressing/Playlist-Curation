import os
import json
from datetime import datetime

from app.config import BASE_DATA_DIR
from app.llm import explain_playlist

def session_agent(state):
    user_id = state["user_id"]
    playlist = state["playlist"]
    prefs = state["preferences"]

    user_dir = os.path.join(BASE_DATA_DIR, "users", user_id)
    log_path = os.path.join(user_dir, "session_log.json")

    if os.path.exists(log_path):
        log = json.load(open(log_path))
    else:
        log = []

    log.append({
        "timestamp": datetime.utcnow().isoformat(),
        "playlist_version": playlist["version"],
        "track_count": len(playlist["tracks"])
    })
    json.dump(log, open(log_path, "w"), indent=2)

    explanation = explain_playlist(
        prefs,
        playlist["new_tracks"],
        playlist["kept_tracks"],
        playlist["removed_tracks"]
    )

    state["session_info"] = {
        "playlist_version": playlist["version"],
        "sessions_count": len(log),
        "explanation": explanation
    }
    return state
