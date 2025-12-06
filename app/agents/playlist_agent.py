# app/agents/playlist_agent.py
import os
import json
from typing import Dict, Any, List, Tuple

from app.config import BASE_DATA_DIR


def _tracks_from_artist_recordings(
    recordings: Dict[str, Any],
    display_artist: str,
    max_tracks: int,
    source_label: str,
) -> List[Dict[str, Any]]:
    """
    Convert MusicBrainz recordings JSON into our internal track objects.
    Deduplicate by title for that artist.
    """
    tracks: List[Dict[str, Any]] = []
    seen_titles = set()

    for r in recordings.get("recordings", []):
        title = (r.get("title") or "").strip()
        if not title:
            continue

        key = title.lower()
        if key in seen_titles:
            continue  # avoid multiple releases of same song
        seen_titles.add(key)

        tracks.append(
            {
                "artist": display_artist,
                "title": title,
                "mbid": r.get("id", ""),
                "source": source_label,
                "release_date": r.get("first-release-date"),
            }
        )
        if len(tracks) >= max_tracks:
            break
    return tracks


def _extract_tracks(research: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build playlist:
      - Up to 5 tracks per seed artist
      - Up to 3 tracks per similar artist
    """
    playlist: List[Dict[str, Any]] = []

    # Seed artists
    for seed_name, data in research.get("seed_artists", {}).items():
        recs = data.get("recordings", {})
        playlist.extend(
            _tracks_from_artist_recordings(
                recs,
                display_artist=seed_name,
                max_tracks=5,
                source_label="MB recording (seed)",
            )
        )

    # Similar artists
    for key, data in research.get("similar_artists", {}).items():
        sim_name = data.get("name")
        if not sim_name:
            continue
        recs = data.get("recordings", {})
        playlist.extend(
            _tracks_from_artist_recordings(
                recs,
                display_artist=sim_name,
                max_tracks=3,
                source_label="MB recording (similar)",
            )
        )

    # Global dedupe by (artist, title)
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for t in playlist:
        k = (t["artist"].lower(), t["title"].lower())
        if k not in seen:
            seen.add(k)
            deduped.append(t)

    return deduped


def _load_last_playlist(user_dir: str) -> Tuple[int, List[Dict[str, Any]]]:
    playlists_dir = os.path.join(user_dir, "playlists")
    if not os.path.isdir(playlists_dir):
        return 0, []

    files = sorted(
        [f for f in os.listdir(playlists_dir) if f.startswith("playlist_v")],
        key=lambda x: int(x.split("playlist_v")[-1].split(".")[0]),
    )
    if not files:
        return 0, []

    latest = files[-1]
    version = int(latest.split("playlist_v")[-1].split(".")[0])
    with open(os.path.join(playlists_dir, latest), "r", encoding="utf-8") as f:
        playlist = json.load(f)
    return version, playlist


def _diff(old: List[Dict[str, Any]], new: List[Dict[str, Any]]):
    def key(t):
        return (t.get("artist"), t.get("title"))

    old_map = {key(t): t for t in old}
    new_map = {key(t): t for t in new}

    new_keys = set(new_map) - set(old_map)
    kept_keys = set(new_map) & set(old_map)
    removed_keys = set(old_map) - set(new_map)

    new_tracks = [new_map[k] for k in new_keys]
    kept_tracks = [new_map[k] for k in kept_keys]
    removed_tracks = [old_map[k] for k in removed_keys]

    return new_tracks, kept_tracks, removed_tracks


def playlist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    user_id = state["user_id"]
    research = state.get("research", {})

    user_dir = os.path.join(BASE_DATA_DIR, "users", str(user_id))
    playlists_dir = os.path.join(user_dir, "playlists")
    os.makedirs(playlists_dir, exist_ok=True)

    old_version, old_playlist = _load_last_playlist(user_dir)

    new_playlist = _extract_tracks(research)

    version = old_version + 1
    path = os.path.join(playlists_dir, f"playlist_v{version}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(new_playlist, f, indent=2, ensure_ascii=False)

    new_tracks, kept_tracks, removed_tracks = _diff(old_playlist, new_playlist)

    state["playlist"] = {
        "version": version,
        "tracks": new_playlist,
        "new_tracks": new_tracks,
        "kept_tracks": kept_tracks,
        "removed_tracks": removed_tracks,
    }
    return state
