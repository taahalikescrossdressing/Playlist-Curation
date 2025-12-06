# app/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.graphs.music_graph import MusicDiscoveryGraph
from app.models.schemas import RunRequest, RunResponse, PlaylistTrack

app = FastAPI(title="MusicBrainz AI Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
app.mount("/static", StaticFiles(directory="app/frontend"), name="static")


@app.get("/")
def root():
    return FileResponse("app/frontend/index.html")


graph = MusicDiscoveryGraph()


def to_track(t: dict) -> PlaylistTrack:
    return PlaylistTrack(
        artist=t.get("artist", "Unknown artist"),
        title=t.get("title", "Untitled"),
        source=t.get("source", "musicbrainz_recording"),
        mbid=t.get("mbid", ""),
        release_date=t.get("release_date"),
    )


@app.post("/api/run", response_model=RunResponse)
def run_recommender(req: RunRequest):
    # Convert Pydantic model to plain dict
    prefs_dict = req.preferences.dict()
    state = graph.run(req.user_id, prefs_dict)

    playlist_state = state["playlist"]
    session_info = state["session_info"]

    return RunResponse(
        playlist_version=playlist_state["version"],
        playlist=[to_track(x) for x in playlist_state["tracks"]],
        new_tracks=[to_track(x) for x in playlist_state["new_tracks"]],
        kept_tracks=[to_track(x) for x in playlist_state["kept_tracks"]],
        removed_tracks=[to_track(x) for x in playlist_state["removed_tracks"]],
        explanation=session_info["explanation"],
        sessions_count=session_info["sessions_count"],
    )
