from typing import List, Optional
from pydantic import BaseModel

class Preferences(BaseModel):
    artists: List[str] = []
    genres: List[str] = []
    mood: Optional[str] = None

class RunRequest(BaseModel):
    user_id: str
    preferences: Preferences

class PlaylistTrack(BaseModel):
    artist: str
    title: str
    source: str
    mbid: str
    release_date: Optional[str] = None

class RunResponse(BaseModel):
    playlist_version: int
    playlist: List[PlaylistTrack]
    new_tracks: List[PlaylistTrack]
    kept_tracks: List[PlaylistTrack]
    removed_tracks: List[PlaylistTrack]
    explanation: str
    sessions_count: int
